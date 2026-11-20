"""Консольный клиент DailyInfo."""
import argparse
import logging
import re
import sys
from datetime import date, datetime, time

from lxml import etree
from requests.exceptions import RequestException
from zeep import Client
from zeep.exceptions import Error
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport

SOURCES = {
    "cbr": "https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL",
    "local": "http://127.0.0.1:8000/DailyInfoWebServ/DailyInfo.asmx?wsdl",
}


def currency(value: str) -> str:
    if not re.fullmatch("[A-Za-z]{3}", value):
        raise argparse.ArgumentTypeError("нужен код из трёх латинских букв")
    return value.upper()


def calendar_date(value: str) -> date:
    try:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            return date.fromisoformat(value)
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("нужна дата в формате ГГГГ-ММ-ДД")


def arguments() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--source", choices=SOURCES, default=argparse.SUPPRESS)
    common.add_argument("--xml", action="store_true", default=argparse.SUPPRESS)
    parser = argparse.ArgumentParser(description=__doc__, parents=[common])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("latest", parents=[common])
    rates = commands.add_parser("rates", parents=[common])
    rates.add_argument("--date", type=calendar_date)
    rates.add_argument("--codes", nargs="+", type=currency)
    args = parser.parse_args()
    args.source = getattr(args, "source", "cbr")
    args.xml = getattr(args, "xml", False)
    return args


def print_xml(history: HistoryPlugin) -> None:
    for title, entry in (("Запрос", history.last_sent),
                         ("Ответ", history.last_received)):
        xml = etree.tostring(entry["envelope"], pretty_print=True,
                             encoding="unicode")
        print(title, xml[:3500].rstrip(), sep="\n")
        if len(xml) > 3500:
            print("[продолжение ответа сокращено]")


def print_rates(root: etree._Element, codes: list[str] | None) -> None:
    fields = ("VchCode", "Vnom", "Vname", "Vcurs", "VunitRate")
    rows = [("Код", "Номинал", "Название", "Курс, руб.", "За 1 ед., руб.")]
    for item in root.findall("ValuteCursOnDate"):
        row = tuple(item.findtext(field, "").strip() for field in fields)
        if not codes or row[0] in codes:
            rows.append(row)
    widths = [max(map(len, column)) for column in zip(*rows)]
    for row in rows:
        print("  ".join(value.ljust(width) if i in (0, 2)
                        else value.rjust(width)
                        for i, (value, width) in enumerate(zip(row, widths))))
    missing = set(codes or []) - {row[0] for row in rows[1:]}
    if missing:
        print("Нет курсов для кодов:", ", ".join(sorted(missing)))
    elif len(rows) == 1:
        print("На выбранную дату курсов нет.")


def main() -> int:
    args = arguments()
    url = SOURCES[args.source]
    label = "Банк России" if args.source == "cbr" else "тестовые данные"
    history = HistoryPlugin()
    try:
        client = Client(url, transport=Transport(timeout=12, operation_timeout=20),
                        plugins=[history])
        when = getattr(args, "date", None)
        if when is None:
            when = client.service.GetLatestDateTime().date()
            if args.xml:
                print_xml(history)
        print(f"Источник: {label} | Адрес: {url} | Дата: {when:%d.%m.%Y}")
        if args.command == "rates":
            data = client.service.GetCursOnDateXML(
                On_date=datetime.combine(when, time.min))
            if args.xml:
                print_xml(history)
            # Для xsd:anyType zeep возвращает список дочерних узлов.
            if isinstance(data, list):
                data = next((node for node in data if node.tag == "ValuteData"), None)
            if data is None:
                print("На выбранную дату курсов нет.")
            else:
                print_rates(data, args.codes)
    except (RequestException, Error, etree.XMLSyntaxError) as exc:
        print(f"Ошибка обращения к сервису {url}", file=sys.stderr)
        print(f"Проверьте адрес и доступность сервера ({type(exc).__name__}).",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    logging.getLogger("zeep.wsdl.bindings.soap").setLevel(logging.ERROR)
    sys.exit(main())
