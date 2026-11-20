# Лабораторная работа № 1. SOAP-сервисы

Консольный клиент получает дату последних курсов и таблицу курсов DailyInfo. Один параметр переключает его между Банком России и учебной службой.

## Запуск в Windows

Команды выполняются из папки проекта. Используйте Python 3.11. У spyne 2.14.0 на Python 3.13 возникает ошибка импорта `spyne.util.six.moves`. Если зависимости ещё не установлены, выполните `py -3.11 -m pip install -r requirements.txt`.

```powershell
py -3.11 cbr_client.py latest
py -3.11 cbr_client.py rates --date 2026-11-18 --codes USD EUR CNY
py -3.11 cbr_client.py --xml latest
```

Для проверки учебного источника запустите сервер в отдельной консоли.

```powershell
py -3.11 fake_cbr_service.py
```

Во второй консоли выполните команды клиента.

```powershell
py -3.11 cbr_client.py --source local latest
py -3.11 cbr_client.py --source local rates --codes USD EUR JPY
```

Локальный WSDL доступен по адресу <http://127.0.0.1:8000/DailyInfoWebServ/DailyInfo.asmx?wsdl>. Учебная таблица содержит шесть валют за 18.11.2026. Для других дат сервис вернёт пустую таблицу. Без `--date` клиент сам запрашивает последнюю дату, без `--codes` выводит все валюты. Для проверки ошибки остановите сервер сочетанием Ctrl+C и повторите локальный запрос.
