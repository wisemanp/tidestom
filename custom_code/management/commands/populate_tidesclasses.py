'''Some code to populate the database with the tides classes and linked subclasses'''

from django.core.management.base import BaseCommand
from ...models import TidesClass, TidesClassSubClass

class Command(BaseCommand):
    help = 'Populate TidesClass and TidesClassSubClass models with initial data'

    def handle(self, *args, **kwargs):
        # Create main classes
        sn, _ = TidesClass.objects.get_or_create(name='SN')
        sni, _ = TidesClass.objects.get_or_create(name='SNI')
        snia, _ = TidesClass.objects.get_or_create(name='SNIa')
        snibc, _ = TidesClass.objects.get_or_create(name='SNIbc')
        snib, _ = TidesClass.objects.get_or_create(name='SNIb')
        snic, _ = TidesClass.objects.get_or_create(name='SNIc')
        snid, _ = TidesClass.objects.get_or_create(name='SNId')
        snie, _ = TidesClass.objects.get_or_create(name='SNIe')
        snii, _ = TidesClass.objects.get_or_create(name='SNII')
        slsni, _ = TidesClass.objects.get_or_create(name='SLSN-I')
        slsnii, _ = TidesClass.objects.get_or_create(name='SLSN-II')
        tde, _ = TidesClass.objects.get_or_create(name='TDE')
        kn, _ = TidesClass.objects.get_or_create(name='KN')
        agn, _ = TidesClass.objects.get_or_create(name='AGN')
        lrn, _ = TidesClass.objects.get_or_create(name='LRN')
        cv, _ = TidesClass.objects.get_or_create(name='CV')
        lbv, _ = TidesClass.objects.get_or_create(name='LBV')
        other, _ = TidesClass.objects.get_or_create(name='Other')

        '''# Create sub-classes
        sub_classes = [
            (snia, 'SNIa-91bg-like'),
            (snia, 'SNIa-19T-like'),
            (snia, 'SNIa-02cx-like'),
            (snia, 'SNIa-03fg-like'),
            (snib, 'SNIb-CaST'),
            (snii, 'SNIIn'),
            (snii, 'SNIIb'),
            (snib, 'SNIbn'),
            (snic, 'SNIcn'),
            (snid, 'SNIdn'),
            (snie, 'SNIen'),
            (slsnii, 'SLSN-IIn'),
            (tde, 'TDE-H'),
            (tde, 'TDE-He'),
            (tde, 'TDE-H+He'),
            (tde, 'TDE-Featureless'),
            (tde, 'TDE-BFF'),
        
        ]'''
        TidesClassSubClass.objects.get_or_create(main_class=snia, sub_class='SNIa-norm')
        TidesClassSubClass.objects.get_or_create(main_class=snia, sub_class='SNIa-91bg-like')
        TidesClassSubClass.objects.get_or_create(main_class=snia, sub_class='SNIa-91T-like')
        TidesClassSubClass.objects.get_or_create(main_class=snia, sub_class='SNIa-02cx-like')
        TidesClassSubClass.objects.get_or_create(main_class=snia, sub_class='SNIa-03fg-like')
        TidesClassSubClass.objects.get_or_create(main_class=snib, sub_class='SNIb-CaST')
        TidesClassSubClass.objects.get_or_create(main_class=snii, sub_class='SNIIn')
        TidesClassSubClass.objects.get_or_create(main_class=snii, sub_class='SNIIb')
        TidesClassSubClass.objects.get_or_create(main_class=snic, sub_class='SNIcn')
        TidesClassSubClass.objects.get_or_create(main_class=snid, sub_class='SNIdn')
        TidesClassSubClass.objects.get_or_create(main_class=snie, sub_class='SNIen')
        TidesClassSubClass.objects.get_or_create(main_class=slsnii, sub_class='SLSN-IIn')
        TidesClassSubClass.objects.get_or_create(main_class=snib, sub_class='SNIbn')
        TidesClassSubClass.objects.get_or_create(main_class=snic, sub_class='SNIcn')
        TidesClassSubClass.objects.get_or_create(main_class=snid, sub_class='SNIdn')
        TidesClassSubClass.objects.get_or_create(main_class=snie, sub_class='SNIen')
        self.stdout.write(self.style.SUCCESS('Successfully populated TidesClass and TidesClassSubClass models'))