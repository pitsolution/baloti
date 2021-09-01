from django.db import models
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.urls import path, reverse
from django import forms, http

from .models import Language, Text

class InlineChangeList(object):
    can_show_all = True
    multi_page = True
    get_query_string = ChangeList.__dict__['get_query_string']

    def __init__(self, request, page_num, paginator):
        self.show_all = 'all' in request.GET
        self.page_num = page_num
        self.paginator = paginator
        self.result_count = paginator.count
        self.params = dict(request.GET.items())


class PaginatedTabularInline(admin.TabularInline):
    per_page = 100
    template = 'admin/edit_inline/tabular_paginated.html'
    extra = 0
    can_delete = True

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super(PaginatedTabularInline, self).get_formset(
            request, obj, **kwargs)
        class PaginationFormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super(PaginationFormSet, self).__init__(*args, **kwargs)

                qs = self.queryset.order_by('pk')
                paginator = Paginator(qs, self.per_page)
                try:
                    page_num = int(request.GET.get('page', ['0'])[0])
                except ValueError:
                    page_num = 0

                try:
                    page = paginator.page(page_num + 1)
                except (EmptyPage, InvalidPage):
                    page = paginator.page(paginator.num_pages)

                self.page = page
                self.cl = InlineChangeList(request, page_num, paginator)
                self.paginator = paginator

                if self.cl.show_all:
                    self._queryset = qs
                else:
                    self._queryset = page.object_list

        PaginationFormSet.per_page = self.per_page
        return PaginationFormSet


class TextAdmin(PaginatedTabularInline):
    model = Text
    fields = ('key', 'val', 'nval')
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={'rows': 4, 'cols': 40})
        }
    }


class LanguageAdmin(admin.ModelAdmin):
    model = Language
    inlines = [TextAdmin]
    list_display = ('name', 'site')
    fields = ('name', 'iso', 'site')
    readonly_fields = ('site',)
    change_list_template = 'admin/djlang_load_form.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = path('load/', self.admin_site.admin_view(self.load), name='djlang_load')
        return [my_urls] + urls

    def create_text(self, **kw):
        print(f'creating {dict(**kw)}')
        Text.objects.create(**kw)

    def load(self, request):
        import json
        import requests
        from django.contrib import messages
        try:
            res = requests.get(request.GET.get('q'))
            data = json.loads(res.content)
            for t in data:
                try:
                    t.pop('id')
                    existing = Text.objects.get(language_id=t['language_id'], key=t['key'])
                    ex_dict = dict(
                        key=existing.key,
                        val=existing.val,
                        nval=existing.nval,
                        language_id=existing.language_id
                    )
                    if ex_dict == t:
                        continue
                    print(f'found new {dict(**t)}')
                except Text.DoesNotExist:
                    self.create_text(**t)
                except Text.MultipleObjectsReturned:
                    print('purge')
                    Text.objects.filter(language_id=t['language_id'], key=t['key']).delete()
                    self.create_text(**t)
                else:
                    print('updating')
                    existing.val = t['val']
                    existing.nval = t['nval']
                    existing.save()

            messages.success(request, 'Lang data loaded successfully')
        except Exception as e:
            messages.error(request, 'Could not load lang data')

        return http.HttpResponseRedirect(reverse('admin:djlang_language_changelist'))

admin.site.register(Language, LanguageAdmin)
