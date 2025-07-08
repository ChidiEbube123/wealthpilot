from django.core.management.base import BaseCommand
from main.models import PortfolioModel, AllocationModel
from main.services import PortfolioService

class Command(BaseCommand):
    help = 'Rebalance portfolios based on current data'

    def handle(self, *args, **kwargs):
        portfolios = PortfolioModel.objects.all()
        for p in portfolios:
            tickers = " ".join([a.ticker for a in p.allocations.all()])
            service = PortfolioService(tickers, p.expected_return).create()
            p.expected_risk = service.expected_risk
            p.save()

            p.allocations.all().delete()
            for alloc in service.allocations:
                AllocationModel.objects.create(
                    portfolio=p,
                    ticker=alloc["ticker"],
                    percentage=alloc["percentage"]
                )

        self.stdout.write("Rebalanced all portfolios.")
