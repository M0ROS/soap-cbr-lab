"""Учебная служба DailyInfo, SOAP 1.1."""
import logging
from datetime import datetime
from decimal import Decimal
from wsgiref.simple_server import make_server

from lxml import etree
from spyne import AnyXml, Application, DateTime, ServiceBase, rpc
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

NAMESPACE = "http://web.cbr.ru/"
PATH = "/DailyInfoWebServ/DailyInfo.asmx"
LATEST = datetime(2026, 11, 18)
# Курс в рублях указан за номинал, все значения учебные.
RATES = (
    ("USD", "840", "Доллар США", 1, "81.2340"),
    ("EUR", "978", "Евро", 1, "92.5000"),
    ("CNY", "156", "Китайский юань", 1, "11.4560"),
    ("JPY", "392", "Японских иен", 100, "52.3000"),
    ("KZT", "398", "Казахстанских тенге", 100, "16.2000"),
    ("CHF", "756", "Швейцарский франк", 1, "99.1200"),
)


class DailyInfo(ServiceBase):
    @rpc(_returns=DateTime)
    def GetLatestDateTime(ctx) -> datetime:
        logging.info("GetLatestDateTime()")
        return LATEST

    @rpc(DateTime(min_occurs=1, nillable=False), _returns=AnyXml)
    def GetCursOnDateXML(ctx, On_date: datetime) -> etree._Element:
        logging.info("GetCursOnDateXML(On_date=%s)", On_date.isoformat())
        root = etree.Element("ValuteData", OnDate=On_date.strftime("%Y%m%d"),
                             source="training")
        if On_date.date() != LATEST.date():
            return root
        for code, number, name, nominal, rate in RATES:
            item = etree.SubElement(root, "ValuteCursOnDate")
            unit = Decimal(rate) / nominal
            for tag, value in (("Vname", name), ("Vnom", str(nominal)),
                               ("Vcurs", rate), ("Vcode", number),
                               ("VchCode", code), ("VunitRate", str(unit))):
                etree.SubElement(item, tag).text = value
        return root


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    app = Application([DailyInfo], tns=NAMESPACE, name="DailyInfo",
                      in_protocol=Soap11(validator="lxml"), out_protocol=Soap11())
    with make_server("127.0.0.1", 8000, WsgiApplication(app)) as server:
        logging.info("DailyInfo: http://127.0.0.1:8000%s?wsdl", PATH)
        server.serve_forever()


if __name__ == "__main__":
    main()
