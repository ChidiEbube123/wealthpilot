from django.contrib import admin
from .models import PortfolioModel,UserProfile,RiskProfile
admin.site.register(PortfolioModel)
admin.site.register(UserProfile)
admin.site.register(RiskProfile)


'''
# Register your models here.
admin.site.register(Portfolio)
admin.site.register(UserProfile)
admin.site.register(Allocation)'''