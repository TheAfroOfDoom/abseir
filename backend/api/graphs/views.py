"""
Endpoints to create, list, and retrieve individual graphs.
"""
import operator

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from abseir import grapher

# from .permissions import IsUserOrReadOnly
from .models import Circulant, Complete
from .serializers import (
    CirculantGraphDataSerializer,
    CirculantGraphSerializer,
    CompleteGraphDataSerializer,
    CompleteGraphSerializer,
)


class _GraphViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (AllowAny,)


class _GraphDataViewSet(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (AllowAny,)


class CirculantGraphViewSet(_GraphViewSet):
    """
    Creates and lists circulant graphs. Does not return the raw data for graphs.

    To access graph raw data, see `CirculantGraphDataViewSet`.
    """

    queryset = Circulant.objects.all()
    serializer_class = CirculantGraphSerializer

    def perform_create(self, serializer: CirculantGraphSerializer):
        order, jumps = operator.itemgetter("order", "jumps")(serializer.initial_data)
        graph = grapher.circulant_graph(order, jumps)

        serializer.save(data=graph.to_binary())


class CirculantGraphDataViewSet(_GraphDataViewSet):
    """Retrieves the data of circulant graphs."""

    queryset = Circulant.objects.all()
    serializer_class = CirculantGraphDataSerializer

    # TODO: Consider modifying `.retrieve()` to return data in the format of an image/.adjlist


class CompleteGraphViewSet(_GraphViewSet):
    """
    Creates and lists complete graphs. Does not return the raw data for graphs.

    To access graph raw data, see `CompleteGraphDataViewSet`.
    """

    queryset = Complete.objects.all()
    serializer_class = CompleteGraphSerializer

    def perform_create(self, serializer: CompleteGraphSerializer):
        order = operator.itemgetter("order")(serializer.initial_data)
        graph = grapher.complete_graph(order)

        serializer.save(data=graph.to_binary())


class CompleteGraphDataViewSet(_GraphDataViewSet):
    """Retrieves the data of complete graphs."""

    queryset = Complete.objects.all()
    serializer_class = CompleteGraphDataSerializer

    # TODO: Consider modifying `.retrieve()` to return data in the format of an image/.adjlist
