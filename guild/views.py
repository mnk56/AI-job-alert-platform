from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .models import Company, InterviewSession, ChatLog
from .forms import CompanyForm
from django.contrib import messages
from services import interviewer, evaluator
from django.utils import timezone
from django.db.models import Avg, Count, Q



def index(request):
    """トップページ。登録された会社の一覧を表示する。"""
    companies = Company.objects.all()
    context = {
        'title': 'エージェント・ギルド',
        'companies': companies,
    }
    return render(request, 'guild/index.html', context)


@login_required
def company_create(request):
    """会社を新規登録する。"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            form.save_m2m()
            return redirect('guild:company_detail', pk=company.pk)
    else:
        form = CompanyForm()
    return render(request, 'guild/company_form.html', {'form': form})


def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    return render(request, 'guild/company_detail.html', {'company': company})


@login_required
@require_POST
def session_start(request, company_pk):
    """指定された会社に対して、ログインユーザーの面接を開始する。"""
    company = get_object_or_404(Company, pk=company_pk)
    session = InterviewSession.objects.create(
        company=company,
        challenger=request.user,
        # status はデフォルトで 'in_progress'
    )
    return redirect('guild:session_detail', pk=session.pk)


def session_detail(request, pk):
    """面接セッションの詳細。company と challenger を select_related で JOIN 取得(N+1対策、パート6参照)。"""
    session = get_object_or_404(
        InterviewSession.objects.select_related('company', 'challenger'),
        pk=pk,
    )
    return render(request, 'guild/session_detail.html', {'session': session})
@login_required
@require_POST
def chatlog_post(request, session_pk):
    """挑戦者の発言を保存し、AI面接官の返答を生成して保存する。"""
    session = get_object_or_404(InterviewSession, pk=session_pk)
    message = request.POST.get('message', '').strip()
    
    if message:
        # 1) 挑戦者の発言を保存
        ChatLog.objects.create(session=session, role='challenger', message=message)
        
        # 2) AIの返答を生成して保存。外部サービスは失敗しうるので try/except で守る
        try:
            reply = interviewer.generate_reply(session)
            ChatLog.objects.create(session=session, role='interviewer', message=reply)
        except Exception:
            messages.error(request, 'AI面接官の応答に失敗しました。もう一度お試しください。')
            
    return redirect('guild:session_detail', pk=session.pk)

@login_required
@require_POST
def session_finish(request, pk):
    """面接を終了し、AI に合否判定させて結果を保存する。"""
    session = get_object_or_404(InterviewSession, pk=pk)
    result = evaluator.evaluate(session) # 検証済み dict か None
    if result is None:
        messages.error(request, 'AIの判定結果を読み取れませんでした。もう一度お試しください。')
        return redirect('guild:session_detail', pk=session.pk)
    session.score = result['score']
    session.status = 'passed' if result['passed'] else 'failed'
    session.judge_comment = result['comment']
    session.finished_at = timezone.now()
    session.save()
    return redirect('guild:session_detail', pk=session.pk)

def get_difficulty(pass_rate):
    """合格率に基づいて難易度を返すヘルパー関数。"""
    if pass_rate is None:
        return "未定"
    if pass_rate < 0.3:
        return "高難易度"
    if pass_rate < 0.7:
        return "普通"
    return "易しい"

def stats(request):
    """各会社の面接統計を表示する。"""
    companies = Company.objects.annotate(
        total=Count('sessions'),
        finished=Count('sessions', filter=Q(sessions__status__in=['passed', 'failed'])),
        passed=Count('sessions', filter=Q(sessions__status='passed')),
        avg_score=Avg('sessions__score'),
    )
    rows = []
    for c in companies:
        pass_rate = c.passed / c.finished if c.finished else None
        rows.append({
            'company': c,
            'total': c.total,
            'avg_score': c.avg_score,
            'pass_rate_pct': round(pass_rate * 100) if pass_rate is not None else None,
            'difficulty': get_difficulty(pass_rate),
        })
    # 合格率が低い(=難しい)順。未判定(None)は末尾へ
    rows.sort(key=lambda r: (r['pass_rate_pct'] is None, r['pass_rate_pct'] or 0))
    return render(request, 'guild/stats.html', {'rows': rows})