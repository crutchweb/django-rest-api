from django.conf.urls import url, include
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'current_user', views.CurrentUserViewSet, base_name='current_user')
router.register(r'geolocation', views.UserGeolocationViewSet)
router.register(r'exchanges', views.ProfileExchangeViewSet, base_name='profile_exchange')
router.register(r'categories', views.CategoryViewSet, base_name='category')
router.register(r'items_card', views.Items_cardViewSet, base_name='items_card')
router.register(r'dabo_filter', views.DaboFilterViewSet, base_name='dabo_filter')
router.register(r'cities', views.CitiesViewSet, base_name='cities')
router.register(r'tempuploads', views.Items_cardTempUploadViewSet)
# Автокомплит поиска Items_card
router.register(r'autocomplete', views.AutocompleteViewSet, base_name="autocomplete")




urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', obtain_jwt_token),
    # дополнительные api для items_card
    # url(r'^tempuploads/(?P<pk>[0-9]+)$',
    #       views.Items_cardTempUploadViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy' }),
    #       name='tempuploads'),
    url(r'^items_card/(?P<pk>[0-9]+)/ic_photos/',
          views.Items_cardImageViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy' }),
          name='items_card_images-list'),
    url(r'^items_card/ic_photos/(?P<pk>[0-9]+)$',
          views.Items_cardImageDetailViewSet.as_view({ 'get': 'list', 'put': 'update', 'delete': 'destroy' }),
          name='items_card_images-detail'),
    url(r'^ic_attr/(?P<pk>[0-9]+)$',
         views.Items_cardAttrViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy' }),
         name='items_card_attr'),
    url(r'^items_card/ic_attr/(?P<pk>[0-9]+)$',
         views.Items_cardAttrViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy' }),
         name='items_card_attr-detail'),
    url(r'^items_card/ic_attr/ic_cat_attr/(?P<pk>[0-9]+)',
    #url(r'^items_card/ic_attr/(?P<pk>[0-9]+)$',
         views.Items_cardCatAttrViewSet.as_view({'get': 'list',}),
         name='items_card_cat_attr-detail'),
    url(r'^items_card/ic_attr/(?P<pk>[0-9]+)/ic_val_attr$',
        views.Items_cardValAttrViewSet.as_view({'get': 'list',}),
        name='items_card_val_attr-detail'),
    url(r'^items_card/similar/(?P<pk>[0-9]+)/',
        views.Items_cardSimilarViewSet.as_view({'get': 'list'}),
        name='ic_similar'),
    url(r'items_card/(?P<pk>[0-9]+)/exchange',
        views.Items_cardExchangeViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='ic_exchange'),

    # Расширение категорий
    url(r'^categories/(?P<pk>[0-9]+)/child/',
        views.CatChildViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
        name='cat_child-detail'),
    url(r'^categories/cat_attr/(?P<pk>[0-9]+)/',
        views.CatAttrViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
        name='category_attr-detail'),
    url(r'^categories/cat_attr/val/(?P<pk>[0-9]+)/$',
        views.CatValAttrViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
        name='category_val-detail'),

    # Аккаунт
    # url(r'users/(?P<pk>[0-9]+)/geolocation',
    #     views.UserGeolocationViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
    #     name='geolocation'),
    url(r'^users/(?P<pk>[0-9]+)/profile/',
        views.ProfileViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
        name='profileuser-detail'),
    url(r'^users/profile/archive/(?P<pk>[0-9]+)/',
        views.ProfileArchiveViewSet.as_view({'get': 'list', 'put': 'update'}),
        name='profile_archive'),
    url(r'^users/profile/favorites/(?P<pk>[0-9]+)/',
        views.ProfileFavoritesViewSet.as_view({'get': 'list', 'put': 'update'}),
        name='profile_favorites'),
    url(r'^users/profile/cards/(?P<pk>[0-9]+)/',
        views.ProfileCardsViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
        name='profile_cards'),
    url(r'^users/profile/(?P<pk>[0-9]+)/dialogs/',
        views.DialogViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
        name='dialog-detail'),
    url(r'^users/profile/dialogs/(?P<pk>[0-9]+)/messages/',
        views.MessageViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'}),
        name='message'),

    # Настройки пользователя
    url(r'^current_user/(?P<pk>[0-9]+)/',
         views.CurrentUserViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy' }),
         name='current_user'),

]
