# Публикация на GitHub

Локальный репозиторий уже создан в:

```text
C:\Users\user\Documents\steel-frame-designer
```

## Вариант A: через сайт GitHub

1. Открыть https://github.com/new
2. Создать репозиторий `steel-frame-designer`.
3. Рекомендуется выбрать `Private`.
4. Не добавлять README, `.gitignore` и license на сайте, потому что они уже есть локально.
5. После создания выполнить в PowerShell:

```powershell
cd C:\Users\user\Documents\steel-frame-designer
git remote add origin https://github.com/<your-login>/steel-frame-designer.git
git push -u origin main
```

## Вариант B: через GitHub CLI

Сейчас `gh` на компьютере не установлен. Если установить GitHub CLI:

```powershell
winget install GitHub.cli
gh auth login
cd C:\Users\user\Documents\steel-frame-designer
gh repo create steel-frame-designer --private --source . --remote origin --push
```

## После публикации

1. Открыть вкладку Issues.
2. Создать первые задачи из `docs/initial-issues.md`.
3. Для каждой задачи работать через отдельную ветку и Pull Request.
4. В чат можно присылать ссылку на Issue или текст задачи.
