from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    """会社に付けるタグ。1つのタグは複数の会社に付き、1つの会社は複数のタグを持つ。"""
    name = models.CharField(max_length=30, unique=True, verbose_name='タグ名')

    class Meta:
        ordering = ['name']
        verbose_name = 'タグ'
        verbose_name_plural = 'タグ一覧'

    def __str__(self):
        return self.name
class Company(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    tags = models.ManyToManyField(
    Tag,
    related_name='companies', # tag.companies.all() で逆参照
    blank=True, # タグなしでも会社は作れる
    verbose_name='タグ',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class InterviewSession(models.Model):
    STATUS_CHOICES = [
        ('in_progress', '進行中'),
        ('passed', '合格'),
        ('failed', '不合格'),
        ('aborted', '中止')
    ]
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='会社',
    )
    challenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='challenger_sessions',
        verbose_name='挑戦者',
    )
    status = models.CharField(        # ← STATUS_CHOICES → status
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name='ステータス',
    )
    score = models.IntegerField(null=True, blank=True, verbose_name='スコア')
    judge_comment = models.TextField(blank=True, default='', verbose_name='講評')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='開始日時')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='終了日時')

    def __str__(self):                # ← Meta-с гарсан
        return f'{self.company.name} - {self.challenger.username}'

    class Meta:
        ordering = ['-created_at']
        verbose_name = '面談セッション'
        verbose_name_plural = '面談セッション'
class ChatLog(models.Model):
    """1つの InterviewSession に紐づく、1つの発言。"""
    ROLE_CHOICES = [
        ('interviewer', '面接官(AI)'),
        ('challenger', '挑戦者'),
    ]
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='chatlogs',
        verbose_name='面接セッション',
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name='発言者',
    )
    message = models.TextField(verbose_name='発言内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='発言日時')

    class Meta:
        ordering = ['created_at']
        verbose_name = '発言ログ'
        verbose_name_plural = '発言ログ一覧'

    def __str__(self):
        return f'{self.get_role_display()}: {self.message[:30]}'
    
