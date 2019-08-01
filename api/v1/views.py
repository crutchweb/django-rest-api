from rest_framework import viewsets, status, generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, \
    DjangoModelPermissionsOrAnonReadOnly, AllowAny
from api.v1 import serializers
from django.contrib.auth.models import User
from django.db.models import Q  #сложные запросы
from categories.models import Category
from items_card.models import Items_card, Items_card_images, Items_card_attr, Items_card_cat_attr, \
    Items_card_val_attr, Items_card_autocomplete, Items_card_viewed, Items_card_favorite, TempUpload, Items_card_complaints

# Account
from daboaccount.models import ProfileUser, Message, Dialog, UserGeolocation
from rest_framework.parsers import MultiPartParser, FormParser

# Exchange
from exchange.models import Exchange

# Для автокомплита
from drf_haystack.filters import HaystackAutocompleteFilter
from drf_haystack.viewsets import HaystackViewSet

# Для фильтра
from django.db.models import Q
import json
from functools import reduce
from operator import and_
import math

# Города
from geo.models import geoCity, geoCountry

#this is api
class CitiesViewSet(viewsets.ModelViewSet):
    queryset = geoCity.objects.all().filter(country_id_id=20)
    serializer_class = serializers.CitiesSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('name_ru', 'country_id_id', 'population', 'ontop',)
    search_fields = ('name_ru',)
    http_method_names = ['get',]

    def get_queryset(self):        
        queryset = super(CitiesViewSet, self).get_queryset()
        return queryset.order_by('-population')


class CurrentUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.CurrentUserSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    http_method_names = ['get', 'post', 'put']
    
    def get_queryset(self):        
        queryset = super(CurrentUserViewSet, self).get_queryset()
        return queryset.filter(id=self.request.user.id)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserFreeSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    http_method_names = ['get',]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('parent_id',)


class CatChildViewSet(CategoryViewSet):

    def get_queryset(self):
        queryset = super(CatChildViewSet, self).get_queryset()
        return queryset.filter(parent__id=self.kwargs.get('pk'))

class CatAttrViewSet(viewsets.ModelViewSet):
    queryset = Items_card_cat_attr.objects.all()
    serializer_class = serializers.Cat_CatAttrSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(CatAttrViewSet, self).get_queryset()
        return queryset.filter(icca_categoryid=self.kwargs.get('pk'))

    def perform_create(self, serializer):
        serializer.save(icca_categoryid=Category.objects.get(id = self.kwargs.get('pk')))


class CatValAttrViewSet(viewsets.ModelViewSet):
    queryset = Items_card_val_attr.objects.all()
    serializer_class = serializers.Cat_ValAttrSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(CatValAttrViewSet, self).get_queryset()
        return queryset.filter(icva_catattr_id=self.kwargs.get('pk'))

    def perform_create(self, serializer):
        serializer.save(icva_catattr_id=Items_card_cat_attr.objects.get(pk=self.kwargs.get('pk')))

# items card
class DaboFilterViewSet(viewsets.ModelViewSet):
    '''
    Пример chained фильтра с логикой ИЛИ и И
    crit1 = Q(attr_set__ica_attr_value__in=[8])
    crit2 = Q(attr_set__ica_attr_value__in=[10,9])
    queryset = Items_card.objects.prefetch_related('images', 'attr_set').filter(crit2).filter(crit1).order_by('pk').distinct('pk')
	'''
    queryset = Items_card.objects.prefetch_related('images', 'attr_set')    
    serializer_class = serializers.Items_cardSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        price_ot = self.request.GET.get('price_ot')
        price_do = self.request.GET.get('price_do')
        cat_id = self.request.GET.get('cat_id')

        filter_options = self.request.GET.get('group')
        json_data = json.loads(filter_options)
        
        queryset = Items_card.objects.prefetch_related('images', 'attr_set')
        for key, value in json_data.items():
        	if value:        		
        		x = list(map(int, value.split(',')))
        		queryset = queryset.filter(Q(attr_set__ica_attr_value__in=x))        		        		
        queryset = queryset.order_by('pk').distinct('pk')        
        
        if price_ot:
            queryset = queryset.filter(ic_coast__gte=price_ot)

        if price_do:
            queryset = queryset.filter(ic_coast__lte=price_do)

        if cat_id:
            queryset = queryset.filter(ic_categoryid_id=cat_id)

        # Тест гео
        if 'pinnedLocation' in self.request.COOKIES:        
            pLat = float(self.request.COOKIES['pinnedLat'])
            pLong = float(self.request.COOKIES['pinnedLong'])
            pRange = int(self.request.COOKIES['pinnedRange'])        
            
            lon1 = pLong-pRange/abs(math.cos(math.radians(pLat))*111.0)
            lon2 = pLong+pRange/abs(math.cos(math.radians(pLat))*111.0)
            lat1 = pLat-(pRange/111.0)
            lat2 = pLat+(pRange/111.0)
            geoquery = queryset.filter(ic_lat__range=(lat1, lat2)).filter(ic_long__range=(lon1, lon2))
            queryset = geoquery

        # queryset = super(DaboFilterViewSet, self).get_queryset()    
        return queryset


class Items_cardViewSet(viewsets.ModelViewSet):
    queryset = Items_card.objects.filter(ic_moderatestatus='PB', ic_userstatus='PB')
    # queryset = Items_card.objects.raw("SELECT * FROM items_card_items_card where ic_moderatestatus='PB' and ic_userstatus='PB' ORDER BY ic_publishdate DESC limit "+limit+" offset "+offset);
    serializer_class = serializers.Items_cardSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('id', 'ic_categoryid', 'ic_parentcategory_id',)
    search_fields = ('ic_name_low', 'ic_description_low')
    http_method_names = ['get', 'post']

    from rest_framework.decorators import detail_route

    def get_queryset(self):
        """
        Выдача товара в зависимости от геопозиции пользователя
        """
        queryset = super(Items_cardViewSet, self).get_queryset()
        # Блок с PostGIS
        # user = self.request.user
        # if user.is_authenticated:            
        #     try:
        #         ugeo = UserGeolocation.objects.get(user=user)
        #     except:
        #         return queryset
        # else:
        #     if not self.request.session.session_key:
        #         self.request.session.save()
        #     ses = self.request.session.session_key
        #     try:
        #         ugeo = UserGeolocation.objects.get(session=ses)
        #     except:
        #         return queryset
        # upoint = ugeo.location
        # uradius = ugeo.radius / 40000 * 360    # перевод радиуса из км в градусы
        # uarea = upoint.buffer(uradius)
        # geoquery = queryset.filter(ic_userid__geolocation__location__within=uarea)
        
        # Тест гео
        if 'pinnedLocation' in self.request.COOKIES:        
            pLat = float(self.request.COOKIES['pinnedLat'])
            pLong = float(self.request.COOKIES['pinnedLong'])
            pRange = int(self.request.COOKIES['pinnedRange'])        
            
            lon1 = pLong-pRange/abs(math.cos(math.radians(pLat))*111.0)
            lon2 = pLong+pRange/abs(math.cos(math.radians(pLat))*111.0)
            lat1 = pLat-(pRange/111.0)
            lat2 = pLat+(pRange/111.0)
            geoquery = queryset.filter(ic_lat__range=(lat1, lat2)).filter(ic_long__range=(lon1, lon2))
            queryset = geoquery        

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        Просмотры +1 для уникльных посещений карточки
        """
        card = super(Items_cardViewSet, self).retrieve(request, *args, **kwargs)
        user = self.request.user
        card_id = Items_card.objects.get(id=self.kwargs.get('pk'))        
        if user.is_authenticated():
            query = Items_card_viewed.objects.filter(icv_card=card_id, icv_user=user)
            if query:
                pass
            else:
                view = Items_card_viewed(icv_card=card_id, icv_user=user)
                
                view.save()
                card_id.ic_viewed += 1
                card_id.save()
        else:
            if not request.session.session_key:
                request.session.save()
            session = request.session.session_key
            query = Items_card_viewed.objects.filter(icv_card=card_id, icv_session=session)
            if query:
                pass
            else:
                Items_card_viewed.objects.create(icv_card=card_id, icv_session=session)
                card_id.ic_viewed += 1
                card_id.save()
        return card

    @detail_route(methods=['get'], permission_classes=[AllowAny], url_path='set-complaint')
    def complaint(self, request, pk=None):
        """
        Пожаловаться на карточку товара
        """
        from rest_framework.response import Response
        card = Items_card.objects.get(pk=self.kwargs.get('pk'))
        serializer = serializers.Items_cardSerializer(card, context={'request': request})
        try:
            user = self.request.user
            compl = list(Items_card_complaints.objects.filter(icc_user=user, icc_card=card))
            if not compl:
                new_compl = Items_card_complaints.objects.create(icc_card=card, icc_user=user)
                card.ic_complaints += 1
                card.save()
            else:
                pass
        except:
            if not request.session.session_key:
                request.session.save()
            session = request.session.session_key
            compl = Items_card_complaints.objects.filter(icc_card=card, icc_session=session)
            if compl:
                pass
            else:
                new_compl = Items_card_complaints.objects.create(icc_card=card, icc_session=session)
                card.ic_complaints += 1
                card.save()
        if card.ic_complaints >= 5:
            card.ic_moderatestatus = 'BL'
            card.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['get'], permission_classes=[AllowAny], url_path='favorite')
    def favorite(self,request, pk=None):
        """
        Добавить в избранное
        """
        from rest_framework.response import Response
        card = Items_card.objects.get(pk=self.kwargs.get('pk'))
        #serializer = serializers.Items_cardSerializer(card, context={'request': request})
        try:
            user = self.request.user
        except:
            return Response(status=status.HTTP_403_FORBIDDEN)
        query = Items_card_favorite.objects.filter(icf_card=card, icf_user=user)
        if query:
            query.delete()
            card.ic_favcount -=1
            card.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            new_fav = Items_card_favorite.objects.create(icf_card=card, icf_user=user)
            card.ic_favcount +=1
            card.save()
            return Response(status=status.HTTP_202_ACCEPTED)


    def perform_create(self, serializer):
       #serializer.save(ic_userid=self.request.user, ic_image=self.request.data.get('img'))
        serializer.save(ic_userid=self.request.user)

class Items_cardSimilarViewSet(viewsets.ModelViewSet):
    queryset = Items_card.objects.filter(ic_moderatestatus='PB', ic_userstatus='PB')
    serializer_class = serializers.Items_cardSimilarSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(Items_cardSimilarViewSet, self).get_queryset()

        try:
            cat_id = Items_card.objects.get(pk=self.kwargs.get('pk')).ic_categoryid.pk
            cat_queryset = queryset.filter(ic_categoryid__id=cat_id)
            queryset = cat_queryset
            return queryset.order_by('?')[:3]
        except AttributeError:
            queryset = Items_card.objects.none()
            return queryset

class Items_cardImageViewSet(viewsets.ModelViewSet):
    queryset = Items_card_images.objects.all()
    serializer_class = serializers.Items_card_imagesSerializer
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(Items_cardImageViewSet, self).get_queryset()
        return queryset.filter(ici_items_card_id__pk=self.kwargs.get('pk'))

    def get_serializer_class(self):
        """
        Выбор сериализатора в зависимости от метода
        """
        if self.action == 'list':
            return serializers.Items_card_imagesSerializer
        else:
            return serializers.Items_card_imagesCreateSerializer

    def perform_create(self, serializer):
        serializer.save(ici_items_card_id=Items_card.objects.get(pk=self.kwargs.get('pk')))

class Items_cardImageDetailViewSet(viewsets.ModelViewSet):
    queryset = Items_card_images.objects.all()
    serializer_class = serializers.Items_card_imagesSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(Items_cardImageDetailViewSet, self).get_queryset()
        return queryset.filter(pk=self.kwargs.get('pk'))

# trash_image
class Items_cardTempUploadViewSet(viewsets.ModelViewSet):
    queryset = TempUpload.objects.all()
    serializer_class = serializers.Items_cardTempUploadSerializer

    # def get_queryset(self):
    #     queryset = super(Items_cardTempUploadViewSet, self).get_queryset()
    #     return queryset.filter(ici_items_card_id__pk=self.kwargs.get('pk'))
    #
    # def perform_create(self, serializer):
    #     serializer.save(ici_items_card_id=Items_card.objects.get(pk=self.kwargs.get('pk')))


class Items_cardAttrViewSet(viewsets.ModelViewSet):
    queryset = Items_card_attr.objects.all()
    serializer_class = serializers.Items_card_attrSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(Items_cardAttrViewSet, self).get_queryset()
        # return queryset.filter(ica_items_card_id__pk=self.kwargs.get('pk'))
        return queryset.filter(ica_items_card_id__pk=self.kwargs.get('pk'))

    def perform_create(self, serializer):
         serializer.save(ica_items_card_id=Items_card.objects.get(pk=self.kwargs.get('pk')))

class Items_cardCatAttrViewSet(viewsets.ModelViewSet):
    queryset = Items_card_cat_attr.objects.all()
    serializer_class = serializers.Ic_CatAttrSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(Items_cardCatAttrViewSet, self).get_queryset()
        return queryset.filter(id=self.kwargs.get('pk'))

    def perform_create(self, serializer):
        serializer.save(icca_categoryid=Items_card.objects.get(id=self.kwargs.get('pk')).ic_categoryid)

class Items_cardValAttrViewSet(viewsets.ModelViewSet):
    queryset = Items_card_val_attr.objects.all()
    serializer_class = serializers.Ic_ValAttrSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(Items_cardValAttrViewSet, self).get_queryset()
        return queryset.filter(id=self.kwargs.get('pk'))

class Items_cardExchangeViewSet(viewsets.ModelViewSet):
    queryset = Exchange.objects.all()
    serializer_class = serializers.ExchangeCardSerialaizer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super(Items_cardExchangeViewSet, self).get_queryset()
        this_card = Items_card.objects.get(id=self.kwargs.get('pk'))
        try:
            user_cards = Items_card.objects.filter(ic_userid=self.request.user)
        except:
            empty_query = queryset.none()
            return empty_query
        else:
            new_query = queryset.filter(Q(desired_card=this_card, suggested_card__in=user_cards)
                                        | Q(desired_card__in=user_cards, suggested_card=this_card))
            return new_query

    def perform_create(self, serializer):
        return serializer.save(desired_card=Items_card.objects.get(id=self.kwargs.get('pk')))

class AutocompleteViewSet(HaystackViewSet):
    """
    Автокомплит поиска для Items_card
    """
    index_models = [Items_card_autocomplete]
    serializer_class = serializers.AutocompleteSerializer
    filter_backends = [HaystackAutocompleteFilter]
    permission_classes = [IsAuthenticated]


# Account
class ProfileViewSet(viewsets.ModelViewSet):
    """
    Аккаунт
    """
    # queryset = ProfileUser.objects.filter(user__is_staff=False)
    queryset = ProfileUser.objects.all()
    serializer_class = serializers.ProfileSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(ProfileViewSet, self).get_queryset()
        return queryset.filter(user__pk=self.kwargs.get('pk'))

class ProfileArchiveViewSet(viewsets.ModelViewSet):
    """
    Архив карточек пользователей
    """
    queryset = Items_card.objects.filter(Q(ic_moderatestatus='FN') | Q(ic_moderatestatus='BL') | Q(ic_userstatus='FN'))
    serializer_class = serializers.Items_cardSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(ProfileArchiveViewSet, self).get_queryset()
        id = ProfileUser.objects.get(pk=self.kwargs.get('pk')).user.pk
        return queryset.filter(ic_userid__pk=id)

class ProfileCardsViewSet(viewsets.ModelViewSet):
    """
    Текущие карточки пользователя
    """
    queryset = Items_card.objects.filter(~Q(ic_moderatestatus='FN') & ~Q(ic_userstatus='FN'))
    serializer_class = serializers.Items_cardSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('id', 'ic_categoryid',)
    http_method_names = ['get', 'post']

    def get_queryset(self):
        queryset = super(ProfileCardsViewSet, self).get_queryset()
        id = ProfileUser.objects.get(pk=self.kwargs.get('pk')).user.pk
        return queryset.filter(ic_userid__pk=id)


class ProfileFavoritesViewSet(viewsets.ModelViewSet):
    """
    Текущие карточки пользователя в избранном
    """
    serializer_class = serializers.Items_cardSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        id = self.kwargs.get('pk')
        queryset = Items_card.objects.raw("select * from items_card_items_card as a left join items_card_items_card_favorite b on a.id=b.icf_card_id where a.ic_moderatestatus != 'FN' and a.ic_userstatus != 'FN' and b.icf_user_id="+str(id))
        return queryset


class ProfileExchangeViewSet(viewsets.ModelViewSet):
    """
    Обмены пользователя
    """
    queryset = Exchange.objects.all()
    serializer_class = serializers.ExchangeProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self):
        queryset = super(ProfileExchangeViewSet, self).get_queryset()
        try:
            user_cards = Items_card.objects.filter(ic_userid=self.request.user)
        except:
            emp_query = queryset.none()
            return emp_query
        else:
            new_query = queryset.filter(Q(desired_card__in=user_cards) | Q(suggested_card__in=user_cards))
            return new_query


class UserGeolocationViewSet(viewsets.ModelViewSet):
    """
    Геолокация пользователя
    """
    queryset = UserGeolocation.objects.all()
    serializer_class = serializers.UserGeolocationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super(UserGeolocationViewSet, self).get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        else:
            if not self.request.session.session_key:
                self.request.session.save()
            return queryset.filter(session=self.request.session.session_key)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            return serializer.save(user=self.request.user)
        else:
            if not self.request.session.session_key:
                self.request.session.save()
            return serializer.save(session=self.request.session.session_key)

class DialogViewSet(viewsets.ModelViewSet):
    """
    Диалоги пользователя
    """
    queryset = Dialog.objects.all()
    # serializer_class = serializers.DialogCreateSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id',)
    # custom_serializer_classes = {
    #     'create': serializers.DialogCreateSerializer,
    #     'update': serializers.DialogCreateSerializer,
    #     'list': serializers.DialogSerializer,
    # }

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.DialogSerializer
        else:
            return serializers.DialogCreateSerializer

    def get_queryset(self):
        queryset = super(DialogViewSet, self).get_queryset()
        user = ProfileUser.objects.get(pk=self.kwargs.get('pk')).user
        return queryset.filter(Q(first_user=user) | Q(second_user=user))

    def perform_create(self, serializer):
        serializer.save(first_user=ProfileUser.objects.get(pk=self.kwargs.get('pk')).user)




class MessageViewSet(viewsets.ModelViewSet):
    """
    Сообщения между пользователями
    """
    queryset = Message.objects.all()
    serializer_class = serializers.MessagesSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        queryset = super(MessageViewSet, self).get_queryset()
        qs=queryset.filter(dialog__id=self.kwargs.get('pk'))
        qsv=queryset.filter(Q(dialog__id=self.kwargs.get('pk')) & ~Q(user__id=self.request.user.id))
        qsv.update(new=False)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, dialog=Dialog.objects.get(id=self.kwargs.get('pk')))

