from rest_framework import generics, permissions, viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from habit.models import Habit, Tracking
from habit.serializers import HabitSerializer, TrackingSerializer


class HabitViewSet(viewsets.GenericViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.habits.all()

    def list(self, request):
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        habit = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(habit)
        return Response(serializer.data)

    def update(self, request, pk=None):
        habit = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(habit, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        habit = get_object_or_404(self.get_queryset(), pk=pk)
        habit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateTrackingView(generics.CreateAPIView):
    queryset = Tracking.objects.all()
    serializer_class = TrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        habit_id = self.request.data.get('habit')
        habit = get_object_or_404(Habit, id=habit_id, user=user)
        serializer.save(habit=habit)
