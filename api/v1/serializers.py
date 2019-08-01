from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer
from api.v1 import base_serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from categories.models import Category
from items_card.models import Items_card, Items_card_favorite, Items_card_images, Items_card_attr, Items_card_cat_attr, Items_card_val_attr, TempUpload
from exchange.models import Exchange
from items_card.search_indexes import Items_cardIndex

from rest_framework.parsers import MultiPartParser, FormParser

# Account
from daboaccount.models import ProfileUser, Message, Dialog, UserGeolocation
# Registration
from rest_auth.registration.serializers import RegisterSerializer
from partner_link.models import Partner
from django.db import connection

# geo
from geo.models import geoCity, geoCountry

# User and Account

class UserGeolocationSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериализатор для записи и хранения последней геопозиции пользователя
    """
    class Meta:
        model = UserGeolocation
        fields = ('pk', 'latitude', 'longitude', 'radius', 'location', 'user', 'session')
        read_only_fields = ('user', 'session', 'location')

    def create(self, validated_data):
        # if validated_data['user'] is None:
        #     ses = validated_data['session']
        #     query = UserGeolocation.objects.filter(session=ses)
        # else:
        #     query = UserGeolocation.objects.filter(user=validated_data['user'])
        try:
            query = UserGeolocation.objects.filter(user=validated_data['user'])
        except KeyError:
            query = UserGeolocation.objects.filter(session=validated_data['session'])
        
        if query:
            current_geo = list(query)[0]
            current_geo.latitude = validated_data['latitude']
            current_geo.longitude = validated_data['longitude']
            current_geo.radius = validated_data['radius']
            current_geo.save()
            return current_geo
        else:
            return super(UserGeolocationSerializer, self).create(validated_data)


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер профиля пользователя
    """
    archive = serializers.HyperlinkedIdentityField(view_name='profile_archive')
    cards = serializers.HyperlinkedIdentityField(view_name='profile_cards')
    dialog = serializers.HyperlinkedIdentityField(view_name='dialog-detail')
    exchange = serializers.SerializerMethodField()
    partner_link = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField(method_name='dialog_unread_count')

    def dialog_unread_count(self, obj):
        try:
            user = self.context['request'].user.id
            with connection.cursor() as cursor:
                cursor.execute('select count(*) from daboaccount_dialog as d inner join daboaccount_message as m on d.id=m.dialog_id where d.second_user_id='+str(user)+' and m.user_id!='+str(user)+' and m."new"=true')
                row = cursor.fetchone()
                return (row)
        except:
            return 0

    class Meta:
        model = ProfileUser
        fields = ('pk', 'url', 'user', 'avatar', 'raiting', 'balance',
                  'address', 'phone', 'date_visit',
                  'archive', 'cards', 'dialog',
                  'exchange', 'partner_link','unread_count')
        read_only_fields = ('raiting', 'balance', 'date_visit', 'archive', 'cards', 'dialog', 'user', 'exchange','unread_count')

    def get_exchange(self, obj):
        """
        Метод для формирования ссылки на api
        """
        from django.urls import reverse
        return self.context['request'].build_absolute_uri(reverse('profile_exchange-list'))

    def get_partner_link(self, obj):
        """
        Формирование полной партнерской ссылки
        """
        return self.context['request'].build_absolute_uri(obj.partner_link)


class PartnerSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер для отображения приглашенных пользователей
    """
    class Meta:
        model = Partner
        fields = ('user', 'parent_bonus')


class CitiesSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер для отображения городов
    """
    class Meta:
        model = geoCity
        fields = ('name_ru', 'name_en', 'population', 'latitude', 'longitude')


class CurrentUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'first_name', 'last_name', 'email')

    def update(self, instance, validated_data):                        
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance


class UserSerializer(serializers.HyperlinkedModelSerializer):
    profileuser = ProfileSerializer()
    geolocation = UserGeolocationSerializer(many=True)
    partners = PartnerSerializer(many=True)

    class Meta:
        model = User
        fields = ('url', 'first_name', 'last_name', 'username', 'password', 'email', 'last_login', 'is_staff',
                  'profileuser', 'pk', 'geolocation', 'partners')
        read_only_fields = ('is_staff', 'last_login',)

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            password=make_password(validated_data['password'])
        )
        user.save()
        return user
    
    def update(self, instance, validated_data):
        print('assa')                
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.save()
        return instance
       

class MessagesSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер для сообщений между пользователями
    """
    class Meta:
        model = Message
        fields = ('pk', 'text', 'user', 'dialog', 'date','new',)
        read_only_fields = ('date', 'user', 'dialog','new')


class DialogSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер для диалогов
    """
    first_user = UserSerializer()
    second_user = UserSerializer()
    unread_count = serializers.SerializerMethodField(method_name='dialog_unread_count')
    create_message = serializers.HyperlinkedIdentityField(view_name='message')
    message = MessagesSerializer(many=True)

    def dialog_unread_count(self, obj):
        try:
            user = self.context['request'].user.id
            dialog = obj.id
            with connection.cursor() as cursor:
                cursor.execute('select count(*) from daboaccount_dialog as d inner join daboaccount_message as m on d.id=m.dialog_id where m.dialog_id='+str(dialog)+' and d.second_user_id='+str(user)+' and m.user_id!='+str(user)+' and m."new"=true')
                row = cursor.fetchone()
                return (row)
        except:
            return 0

    class Meta:
        model = Dialog
        fields = ('pk', 'first_user', 'second_user', 'date', 'message', 'create_message','unread_count')
        read_only_fields = ('date', 'first_user', 'message','unread_count')


class DialogCreateSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер для диалогов
    """

    message = MessagesSerializer(many=True,read_only=True)

    class Meta:
        model = Dialog
        fields = ('pk', 'first_user', 'second_user', 'date', 'message')
        read_only_fields = ('date', 'first_user', 'message')

    def create(self, validated_data):
        """
        Проверка, есть ли подобный диалог
        """
        from django.db.models import Q
        user_1 = validated_data['first_user']
        user_2 = validated_data['second_user']
        query = Dialog.objects.filter(Q(first_user=user_1, second_user=user_2) | Q(first_user=user_2, second_user=user_1))

        if query:
            dialog = list(query)[0]
            return dialog
        else:
            return super(DialogCreateSerializer, self).create(validated_data)


class UserRegisterSerializer(RegisterSerializer):
    """
    Перераспределение базового сериализатора регистрации rest-auth 
    для создании партнеров после создания обЪекта
    """
    def save(self, request):
        user = super(UserRegisterSerializer, self).save(request)
        try:
            parent = User.objects.get(id=request.COOKIES.get('parent_partner'))
            cur_user = User.objects.get(id=user.id)
        except:
            pass
        else:
            from partner_link.models import BonusActions
            BonusActions.bonus_for_regpartn(parent=parent, user=cur_user)
        return user


class ProfileFreeSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер профиля пользователя доступный для всех
    """
    cards = serializers.HyperlinkedIdentityField(view_name='profile_cards')

    class Meta:
        model = ProfileUser
        fields = ('avatar', 'raiting', 'balance',
                  'address', 'phone', 'cards',)


class UserFreeSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериалайзер пользователя доступный для всех
    """
    profileuser = ProfileFreeSerializer()
    geolocation = UserGeolocationSerializer(many=True)

    class Meta:
        model = User
        fields = ('pk', 'url', 'first_name', 'last_name', 'username', 'email',
                  'profileuser', 'geolocation',)


# Category


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    attr = serializers.HyperlinkedIdentityField(view_name='category_attr-detail')
    child = serializers.HyperlinkedIdentityField(view_name='cat_child-detail',)
    parent_id = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('pk', 'name', 'parent', 'parent_id', 'child', 'attr')

    def get_parent_id(self, obj):
        """
        Метод для формирования ссылки на api
        """
        if obj.parent != None:
            return obj.parent.id
        else:
            return ''

class Cat_CatAttrSerializer(base_serializers.CatAttrSerializer):
    values = serializers.HyperlinkedIdentityField(view_name='category_val-detail')
    class Meta:
        model = Items_card_cat_attr
        fields = ('pk', 'url', 'icca_attrname', 'icca_categoryid', 'values')
        read_only_fields = ('icca_categoryid',)

class Cat_ValAttrSerializer(base_serializers.ValAttrSerializer):
    class Meta:
        model = Items_card_val_attr
        fields = '__all__'
        read_only_fields = ('icva_catattr_id',)


# Items card
# class DaboFilterSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Items_card
#         fields = '__all__'

class Ic_CatAttrSerializer(base_serializers.CatAttrSerializer):
    pass

class Ic_ValAttrSerializer(base_serializers.ValAttrSerializer):
    pass

class Items_card_attrSerializer(serializers.HyperlinkedModelSerializer):
    # расширялка

    def get_fields(self, *args, **kwargs):
        """
        Формируем фильтрованную выдачу вторичных ключей в форме
        """
        fields = super(Items_card_attrSerializer, self).get_fields(*args, **kwargs)
        ic_pk = self.context['view'].kwargs.get('pk')
        ic_category = Items_card.objects.get(pk=ic_pk).ic_categoryid
        cat_queryset = fields['ica_cat_attr'].queryset.filter(icca_categoryid=ic_category)
        val_queryset = fields['ica_attr_value'].queryset.filter(icva_catattr_id__icca_categoryid=ic_category)

        fields['ica_cat_attr'].queryset = cat_queryset
        fields['ica_attr_value'].queryset = val_queryset

        return fields

    class Meta:
        model = Items_card_attr
        fields = ('pk', 'ica_cat_attr', 'ica_attr_value', 'ica_items_card_id',)
        read_only_fields = ('ica_items_card_id',)


class Items_card_imagesSerializer(serializers.HyperlinkedModelSerializer):
    """
    Дополнительные изображения к карточке товара
    """
    class Meta:
        model = Items_card_images
        fields = ('url', 'pk', 'ici_items_card_id', 'ici_image', 'ici_thumbnail')

class Items_card_imagesCreateSerializer(serializers.Serializer):
    """
    Одновременная загрузка нескольких изображений
    """
    ici_image = serializers.ListField(min_length=0, max_length=4,
                    child=serializers.FileField(max_length=100000, allow_empty_file=True, use_url=True)
                    )
    def create(self, validated_data):
        """
        Создание нескольких объектов
        """
        images = validated_data.pop('ici_image')
        for img in images:
            ici_image = Items_card_images.objects.create(ici_image=img, **validated_data)
        return ici_image

# Items card
class Items_cardSerializer(serializers.HyperlinkedModelSerializer):
    # расширяем сериалайзер связывая с другим api
    ici_image = serializers.HyperlinkedIdentityField(view_name='items_card_images-list',)
    ica_attr = serializers.HyperlinkedIdentityField(view_name='items_card_attr')
    ic_similar = serializers.HyperlinkedIdentityField(view_name='ic_similar')
    set_complaint = serializers.HyperlinkedIdentityField(view_name='items_card-set-complaint')
    favorite = serializers.HyperlinkedIdentityField(view_name='items_card-favorite')
   # is_favorited = serializers.BooleanField(method_name='check_favorite',read_only=True)
    is_favorited = serializers.SerializerMethodField(method_name='check_favorite')
    exchange = serializers.HyperlinkedIdentityField(view_name='ic_exchange')

    def check_favorite(self, obj):
        try:
            user = self.context['request'].user
            card = obj.id
            query = Items_card_favorite.objects.filter(icf_card=card, icf_user=user)
            if query:
                return True
            return False
        except:
            return False

    class Meta:
        model = Items_card
        fields = ('pk', 'ic_parentcategory_id', 'ic_name', 'ic_shortdescription', 'ic_description', 'ic_coast',
                   'ic_image', 'ic_thumbnail', 'ic_categoryid', 'ic_lat', 'ic_long', 'ici_image', 'ica_attr',
                  'ic_viewed', 'ic_favcount', 'ic_complaints', 'ic_publishdate', 'ic_moderatestatus', 'ic_userstatus', 'ic_type',
                  'ic_userid', 'ic_call', 'ic_free', 'ic_allowexchange', 'ic_similar', 'set_complaint', 'favorite', 'is_favorited' , 'exchange')
        read_only_fields = ('ic_viewed', 'ic_favcount', 'ic_publishdate', 'ic_moderatestatus', 'ic_userid', 'ic_similar', 'is_favorited', 'exchange')

    def to_representation(self, instance):
        data = super(Items_cardSerializer, self).to_representation(instance)
        if (data['ic_type'] != 'EX') and (not data['ic_allowexchange']):
            data.pop('exchange')
        return data

#test!
class Items_cardFavoritesSerializer(serializers.HyperlinkedModelSerializer):
    """
    favorites
    """
    class Meta:
        model = Items_card_favorite
        fields = ('pk','icf_card','icf_user','icf_session',)
#test


class Items_cardSimilarSerializer(serializers.HyperlinkedModelSerializer):
    """
    Похожие карточки
    """
    url = serializers.HyperlinkedIdentityField(view_name='items_card-detail')
    class Meta:
        model = Items_card
        fields = ('pk', 'url', 'ic_name', 'ic_shortdescription', 'ic_thumbnail', 'ic_coast',)

class Items_cardTempUploadSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TempUpload
        fields = '__all__'


class ExchangeCardSerialaizer(serializers.HyperlinkedModelSerializer):
    """
    Обмен для карточки товара
    """
    class Meta:
        model = Exchange
        fields = ('pk', 'desired_card', 'suggested_card', 'status', 'date')
        read_only_fields = ('status', 'desired_card', 'date',)

    def get_fields(self, *args, **kwargs):
        """
        Формируем фильтрованную выдачу вторичных ключей в форме
        """
        fields = super(ExchangeCardSerialaizer, self).get_fields(*args, **kwargs)
        user = self.context['view'].request.user
        card_queryset = fields['suggested_card'].queryset.filter(ic_userid=user, ic_allowexchange=True,
                                                                 ic_moderatestatus='PB', ic_userstatus='PB')
        fields['suggested_card'].queryset = card_queryset
        return fields


class ExchangeProfileSerializer(serializers.HyperlinkedModelSerializer):
    """
    Обмен в профиле юзера
    """
    class Meta:
        model = Exchange
        fields = ('pk', 'desired_card', 'suggested_card', 'status', 'date')
        read_only_fields = ('pk', 'desired_card', 'suggested_card', 'date')

class AutocompleteSerializer(HaystackSerializer):
    """
    Сериалайзер для автокомплита
    """
    class Meta:
        index_classes = [Items_cardIndex,]
        fields = ['name', 'autocomplete']
        ignore_fields = ['autocomplete']

        field_aliases = {
            "q": "autocomplete"
        }


# Account



