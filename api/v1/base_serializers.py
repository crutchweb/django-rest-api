from rest_framework import serializers
from items_card.models import Items_card_cat_attr, Items_card_val_attr

# Базовые сериализаторы
class CatAttrSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Items_card_cat_attr
        fields = '__all__'

class ValAttrSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Items_card_val_attr
        fields = '__all__'