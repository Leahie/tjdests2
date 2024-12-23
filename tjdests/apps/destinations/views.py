from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from ..authentication.models import User
from .models import College, Decision, TestScore


class StudentDestinationListView(
    LoginRequiredMixin, UserPassesTestMixin, ListView
):  # pylint: disable=too-many-ancestors
    model = User
    paginate_by = 20
    
    def get_queryset(self):
        # Superusers can use the "all" GET parameter to see all data
        print(self.request.GET) 

        # Getting Queryset
        if self.request.GET.get("all", None) is not None:
            if self.request.user.is_superuser and self.request.user.is_staff:
                queryset = User.objects.all()
            else:
                raise PermissionDenied()
        else:
            queryset = User.objects.filter(publish_data=True)

        queryset = queryset.filter(is_senior=True).order_by(
            "last_name", "preferred_name"
        )
        

        #College 
        college_id: Optional[str] = self.request.GET.get("college", None)
        
            
        if college_id is not None and college_id != '':
            if not college_id.isdigit():
                raise Http404()
            get_object_or_404(College, id=college_id)
            queryset = queryset.filter(decision__college__id=college_id)
            # Decision Type 
            decision_type: Optional[str] = self.request.GET.get("decision", None)
            print(decision_type)
            if decision_type is not None and decision_type != '':
                queryset = queryset.filter(decision__decision_type=decision_type)
            
            admission_type: Optional[list] = self.request.GET.getlist("admission")
            if admission_type:  # Check if any admission types were selected
                queryset = queryset.filter(decision__admission_status__in=admission_type)

        # GPA   
        gpa_max: Optional[str] = self.request.GET.get("gpa_max", '')
        gpa_min: Optional[str] = self.request.GET.get("gpa_min", '')

        if gpa_max!='' and gpa_min=='': gpa_min="0"
        if gpa_min!='' and gpa_max=='': gpa_max="5"
        
        if gpa_max!='' and gpa_min!='':
            
            if gpa_min>gpa_max:
                raise Http404()
            
            gpa_min = float(gpa_min) 
            gpa_max = float(gpa_max) 
            
            if gpa_min:
                queryset = queryset.filter(GPA__gte=gpa_min)  # GPA >= gpa_min

            if gpa_max:
                queryset = queryset.filter(GPA__lte=gpa_max)  # GPA <= gpa_max

         # Test Types and Scores Filter
        test_types: Optional[list] = self.request.GET.getlist("test_score", [])
        if test_types:
            queryset = queryset.filter(testscore__exam_type__in=test_types)

        # SAT Filter
        sat_min: Optional[str] = self.request.GET.get("sat_min", '')
        sat_max: Optional[str] = self.request.GET.get("sat_max", '')
        if sat_max != '' and sat_min == '': sat_min = "0"
        if sat_min != '' and sat_max == '': sat_max = "1600"
        if sat_min != '' or sat_max != '':
            if sat_min > sat_max:
                raise Http404("Invalid SAT score range")
            
            sat_min = int(sat_min)  # Default min = 0
            sat_max = int(sat_max)  # Default max = 1600

            sat_filter = Q(testscore__exam_type="SAT_TOTAL")
            if sat_min:
                sat_filter &= Q(testscore__exam_score__gte=sat_min)

            if sat_max:
                sat_filter &= Q(testscore__exam_score__lte=sat_max)

        # ACT Filter
        act_min: Optional[str] = self.request.GET.get("act_min", '')
        act_max: Optional[str] = self.request.GET.get("act_max", '')
        if act_max != '' and act_min == '': act_min = "0"
        if act_min != '' and act_max == '': act_max = "36"
        if act_min != '' or act_max != '':
            if act_min > act_max:
                raise Http404("Invalid ACT score range")
            
            act_min = int(act_min)  # Default min = 0
            act_max = int(act_max)  # Default max = 36

            act_filter = Q(testscore__exam_type="ACT_COMP")
            if act_min:
                act_filter &= Q(testscore__exam_score__gte=act_min)

            if act_max:
                act_filter &= Q(testscore__exam_score__lte=act_max)

        final_filter = Q()

        if sat_min != '' or sat_max != '':
            final_filter |= sat_filter  # Apply SAT filter if SAT is provided

        if act_min != '' or act_max != '':
            final_filter |= act_filter  # Apply ACT filter if ACT is provided

        queryset = queryset.filter(final_filter)
        queryset = queryset.distinct()
        
        print("set", queryset)
        return queryset

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):  # pylint: disable=unused-argument
        context = super().get_context_data(**kwargs)

       
        context['TEST_TYPES'] = TestScore.TEST_TYPES
        context['COLLEGES'] = College.objects.all()
        context['DECISIONS'] = Decision.DECISION_TYPE_CHOICES
        context['ADMISSIONS'] = Decision.ADMIT_TYPE_CHOICES
        
        # College
        college_id: Optional[str] = self.request.GET.get("college", None)
        if college_id is not None and college_id != '':
            context["college"] = get_object_or_404(College, id=college_id)
            # Decision Type
            decision_type: Optional[str] = self.request.GET.get("decision", None)
            if decision_type is not None and decision_type != '':
                context["DECISION"] = decision_type
            admission_type: Optional[list] = self.request.GET.getlist("admission")  # Get all selected admissions
            if admission_type:  # If there's at least one admission type selected
                context["ADMISSION"] = ', '.join(admission_type)    

        # GPA
        gpa_min: Optional[str] = self.request.GET.get("gpa_min", '')
        gpa_max: Optional[str] = self.request.GET.get("gpa_max", '')
        
        if  gpa_min=='': gpa_min="0"
        if gpa_max=='': gpa_max="5"

        context["GPA_MIN"] = gpa_min
        context["GPA_MAX"] = gpa_max
        
        # SAT
        sat_min: Optional[str] = self.request.GET.get("sat_min", "0")
        sat_max: Optional[str] = self.request.GET.get("sat_max", "1600")
        if  sat_min=='': sat_min="0"
        if sat_max=='': sat_max="1600"
        print(sat_min, sat_max)
        context["SAT_MIN"] = sat_min
        context["SAT_MAX"] = sat_max

        # ACT
        act_min: Optional[str] = self.request.GET.get("act_min", "0")
        act_max: Optional[str] = self.request.GET.get("act_max", "36")
        if  act_min=='': act_min="0"
        if act_max=='': act_max="36"
        print(act_min, act_max)
        context["ACT_MIN"] = act_min
        context["ACT_MAX"] = act_max


        # Test Types
        test_types: Optional[list] = self.request.GET.getlist("test_score", '')    
        print(test_types)
        context["SELECTED_TEST_SCORES"] = test_types
        
        search_query = self.request.GET.get("q", None)
        if search_query is not None:
            context["search_query"] = search_query

        return context

    def test_func(self):
        assert self.request.user.is_authenticated
        return self.request.user.accepted_terms and not self.request.user.is_banned

    template_name = "destinations/student_list.html"


class CollegeDestinationListView(
    LoginRequiredMixin, UserPassesTestMixin, ListView
):  # pylint: disable=too-many-ancestors
    model = College
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        search_query = self.request.GET.get("q", None)
        if search_query is not None:
            queryset = College.objects.filter(
                Q(name__icontains=search_query) | Q(location__icontains=search_query)
            )
        else:
            queryset = College.objects.all()

        queryset = (
            queryset.annotate(  # type: ignore  # mypy is annoying
                count_decisions=Count(
                    "decision", filter=Q(decision__user__publish_data=True)
                ),
                count_attending=Count(
                    "decision",
                    filter=Q(
                        decision__in=Decision.objects.filter(
                            attending_college__isnull=False
                        ),
                        decision__user__publish_data=True,
                    ),
                ),
                count_admit=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.ADMIT,
                        decision__user__publish_data=True,
                    ),
                ),
                count_waitlist=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.WAITLIST,
                        decision__user__publish_data=True,
                    ),
                ),
                count_waitlist_admit=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.WAITLIST_ADMIT,
                        decision__user__publish_data=True,
                    ),
                ),
                count_waitlist_deny=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.WAITLIST_DENY,
                        decision__user__publish_data=True,
                    ),
                ),
                count_defer=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.DEFER,
                        decision__user__publish_data=True,
                    ),
                ),
                count_defer_admit=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.DEFER_ADMIT,
                        decision__user__publish_data=True,
                    ),
                ),
                count_defer_deny=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.DEFER_DENY,
                        decision__user__publish_data=True,
                    ),
                ),
                count_defer_wl=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.DEFER_WL,
                        decision__user__publish_data=True,
                    ),
                ),
                count_defer_wl_admit=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.DEFER_WL_A,
                        decision__user__publish_data=True,
                    ),
                ),
                count_defer_wl_deny=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.DEFER_WL_D,
                        decision__user__publish_data=True,
                    ),
                ),
                count_deny=Count(
                    "decision",
                    filter=Q(
                        decision__admission_status=Decision.DENY,
                        decision__user__publish_data=True,
                    ),
                ),
            )
            .filter(count_decisions__gte=1)
            .order_by("name")
        )

        return queryset

    def get_context_data(
        self, *, object_list=None, **kwargs
    ):  # pylint: disable=unused-argument
        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get("q", None)
        if search_query is not None:
            context["search_query"] = search_query

        return context

    def test_func(self):
        assert self.request.user.is_authenticated
        return self.request.user.accepted_terms and not self.request.user.is_banned

    template_name = "destinations/college_list.html"
