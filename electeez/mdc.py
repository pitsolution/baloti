from django.middleware.csrf import get_token
from ryzom import html
from py2js.renderer import JS


class MDCLink(html.A):
    pass


class MDCIcon(html.Icon):
    def __init__(self, icon, **kwargs):
        attrs = {
            'class': 'material-icons',
            'aria-hiddem': 'true'
        }

        if cls := kwargs.pop('cls', None):
            attrs['class'] += f' {cls}'
        super().__init__(icon, **attrs)


class MDCTextButton(html.Button):
    def __init__(self, text, icon=None, **kwargs):
        content = [html.Span(cls='mdc-button__ripple')]
        if icon:
            content.append(MDCIcon(icon))
        content.append(html.Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls='mdc-button',
            **kwargs,
        )


class MDCButtonOutlined(html.Button):
    def __init__(self, text, p=True, icon=None):
        black = 'black-button' if p else ''
        content = [html.Span(cls='mdc-button__ripple')]
        if icon and isinstance(icon, str):
            content.append(MDCIcon(icon))
        elif icon:
            content.append(icon)
        content.append(html.Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls=f'mdc-button mdc-button--outlined {black}'
        )


class MDCButton(html.Button):
    def __init__(self, text, p=True, disabled=False, icon=None):
        black = 'black-button' if p else ''
        attrs = {}
        if disabled:
            attrs['disabled'] = True

        if icon and isinstance(icon, str):
            content = [MDCIcon(icon)]
        elif icon:
            content = [icon]
        else:
            content = []

        content.append(html.Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls=f'mdc-button mdc-button--raised {black}',
            **attrs
        )


class MDCButtonLabelOutlined(html.Label):
    def __init__(self, text, p=True, icon=None):
        black = 'black-button' if p else ''
        content = [html.Span(cls='mdc-button__ripple')]
        if icon:
            content.append(MDCIcon(icon))
        content.append(html.Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls=f'mdc-button mdc-button--outlined {black}'
        )


class MDCTextInput(html.Input):
    def __init__(self, name, **attrs):
        attrs.setdefault('type', 'text')
        attrs.setdefault('class', 'mdc-text-field__input')
        super().__init__(**attrs)


class MDCLabel(html.Span):
    attrs = {'class': 'mdc-floating-label'}


class MDCTextRipple(html.Span):
    def __init__(self):
        super().__init__(**{'class': 'mdc-text-field__ripple'})


class MDCLineRipple(html.Span):
    def __init__(self):
        super().__init__(**{'class': 'mdc-line-ripple'})


class MDCTextFieldFilled(html.Label):
    attrs = {
        'class': 'mdc-text-field mdc-text-field--filled',
    }

    def __init__(self, hint='', input_id='', label_id='', **kwargs):
        content = [
            MDCTextRipple(),
            MDCLabel(hint, label_id),
            MDCTextInput(input_id, **kwargs),
            MDCLineRipple(),
        ]
        super().__init__(*content, **self.attrs)


class MDCNotchOutline(html.Span):
    def __init__(self, *content):
        attrs = {'class': 'mdc-notched-outline'}
        content = [
            html.Span(cls='mdc-notched-outline__leading'),
            html.Span(
                *content,
                cls='mdc-notched-outline__notch',
            ),
            html.Span(cls='mdc-notched-outline__trailing'),
        ]
        super().__init__(*content, **attrs)


class MDCTextFieldOutlined(html.Div):
    def __init__(self, name, **kwargs):
        input_id = f'id_{name}'
        label_id = f'id_{name}_label'
        label = kwargs.pop('label', name.capitalize())
        super().__init__(
            html.Label(
                MDCNotchOutline(
                    html.Span(
                        label,
                        id=label_id,
                        cls='mdc-floating-label',
                    ),
                ),
                MDCTextInput(
                    name=name,
                    aria_labelledby=label_id,
                    id=input_id,
                    **kwargs,
                ),
                cls='mdc-text-field mdc-text-field--outlined',
                data_mdc_auto_init='MDCTextField',
            ),
            cls='form-group'
        )

    def set_error(self, error):
        helper = MDCTextFieldHelperLine(error, 'alert')
        label = self.content[0]
        label.attrs['class'] += ' mdc-text-field--invalid'
        label.attrs['aria-describedby'] = helper._id
        label.attrs['aria-controls'] = helper._id

        self.content.append(helper)


class MDCTextareaFieldOutlined(html.Label):
    def __init__(self, value='', hint='', input_id='', label_id='', **kwargs):
        name = kwargs.get('name', '')
        if not hint:
            hint = name
        if name and not input_id:
            input_id = name + '_input'
        if input_id and not label_id:
            label_id = input_id + '_label'

        if hint:
            label = html.Span(
                html.Span(hint, cls='mdc-floating-label', id=label_id),
                cls='mdc-notched-outline__notch'),
        else:
            label = tuple()

        super().__init__(
            html.Span(
                html.Span(cls='mdc-notched-outline__leading'),
                *label,
                html.Span(cls='mdc-notched-outline__trailing'),
                cls='mdc-notched-outline'
            ),
            html.Span(
                html.Textarea(
                    value,
                    id=input_id,
                    cls='mdc-text-field__input',
                    **{'aria-labelledby': label_id},
                    **kwargs),
                cls='mdc-text-field__resizer'),
            cls='mdc-text-field mdc-text-field--outlined mdc-text-field--textarea',
            **{'data-mdc-auto-init': 'MDCTextField'}
        )


class MDCFormField(html.Div):
    attrs = {'class': 'mdc-form-field'}

    def __init__(self, *content, **kwargs):
        super().__init__(*content, **self.attrs, **kwargs)


class MDCFileInput(html.Div):
    def __init__(self, btn_text='', input_id='', name=''):
        self.btn = MDCButtonLabelOutlined(btn_text, False)
        self.input_id = input_id
        self.btn.attrs['for'] = input_id
        self.selected_text = html.Span('No file selected')
        super().__init__(
            html.Span(
                html.Input(type='file', id=input_id, name=name),
                style='display:block;width:0;height:0;overflow:hidden'
            ),
            self.selected_text,
            self.btn
        )

    def render_js(self):
        def change_event():
            def update_name(event):
                file_name = document.querySelector(input_id).value
                label = getElementByUuid(label_id)

                if file_name != '':
                    setattr(label, 'innerText', file_name)
                else:
                    setattr(label, 'innerText', 'No file selected')


            document.querySelector(input_id).addEventListener('change', update_name)

        return JS(change_event, dict(
            input_id=f'#{self.input_id}',
            label_id=self.selected_text._id,
        ))


class CSRFInput(html.Input):
    def __init__(self, request):
        super().__init__(
            type='hidden',
            name='csrfmiddlewaretoken',
            value=get_token(request)
        )


class MDCSplitDateTime(html.Div):
    def __init__(self, hint='', input_id='', label_id='', **kwargs):
        name = kwargs.pop('name')
        kwargs.pop('type', None)
        value = kwargs.pop('value', None)
        date = value.date() if value else ''
        time = value.time() if value else ''

        super().__init__(
            MDCTextFieldOutlined(
                hint='Date',
                input_id='date_' + name + '_input',
                name=name + '_0',
                value=date,
                type='date',
                **kwargs),
            MDCTextFieldOutlined(
                hint='Time',
                input_id='time_' + name + '_input',
                name=name + '_1',
                value=time,
                type='time',
                **kwargs),
        )

    def set_error(self, error):
        helper = MDCTextFieldHelperLine(error, 'alert')
        label = self.content[1]
        label.attrs['class'] += ' mdc-text-field--invalid'
        label.attrs['aria-describedby'] = helper._id
        label.attrs['aria-controls'] = helper._id

        self.content.append(helper)


class MDCListItem(html.Li):
    def __init__(self, *content, **kwargs):
        cls = kwargs.pop('cls', '')
        super().__init__(
            html.Span(cls='mdc-list-item__ripple'),
            html.Span(*content, cls='mdc-list-item__text'),
            cls=cls + ' mdc-list-item'
        )


class MDCCheckboxListItem(html.Li):
    def __init__(self, title, id, checked=False, **kwargs):
        self.input_id = id
        if checked:
            kwargs['checked'] = True
        super().__init__(
            html.Span(cls='mdc-list-item__ripple'),
            html.Span(
                html.Div(
                    html.Input(
                        id=id,
                        type='checkbox',
                        cls='mdc-checkbox__native-control',
                        **kwargs),
                    html.Div(
                        html.Component(
                            html.Component(
                                tag='path', fill='none',
                                d="M1.73,12.91 8.1,19.28 22.79,4.59",
                                cls='mdc-checkbox__checkmark-path'),
                            tag='svg', viewBox='0 0 24 24',
                            cls='mdc-checkbox__checkmark'),
                        html.Div(cls='mdc-checkbox__mixedmark'),
                        cls='mdc-checkbox__background'),
                    cls='mdc-checkbox'),
                cls='mdc-list-item__graphic'),
            html.Label(title, cls='mdc-list-item__text', **{'for': id}),
            cls='mdc-list-item',
            role='checkbox',
            **{
                'aria-checked': 'true' if checked else 'false',
                'data-list-item-of': id
            }
        )

    def render_js(self):
        def events():
            def click_input(event):
                event.stopPropagation()
                elem = event.target.querySelector('input')
                if elem:
                    elem.click()

            elem = getElementByUuid(id)
            setattr(elem, 'onclick', click_input)

        return JS(events, dict(id=self._id))


class MDCMultipleChoicesCheckbox(html.Ul):
    def __init__(self, name, choices, n=1, **kwargs):
        self.max = n
        alabel = kwargs.pop('aria-label', 'Label')
        super().__init__(
            *(MDCCheckboxListItem(
                title,
                f'{name}_input_{i}',
                name=name,
                value=value,
                **kwargs
            ) for i, title, value in choices),
            cls='mdc-list',
            role='group',
            **{'aria-label': alabel}
        )

    def render_js(self):
        def change_event():
            def update_inputs(event):
                checked = input_list.querySelectorAll('input:checked')
                unchecked = input_list.querySelectorAll('input:not(:checked)')

                def disable(elem, pos, arr):
                    setattr(elem, 'disabled', 'true')
                    list_item = document.querySelector(
                        '[data-list-item-of="' + elem.id + '"]'
                    ).classList.add('mdc-list-item--disabled')

                def enable(elem, pas, arr):
                    setattr(elem, 'disabled', undefined)
                    list_item = document.querySelector(
                        '[data-list-item-of="' + elem.id + '"]'
                    ).classList.remove('mdc-list-item--disabled')

                if checked.length >= max_choices:
                    unchecked.forEach(disable)
                else:
                    unchecked.forEach(enable)

            input_list = getElementByUuid(id)
            input_list.addEventListener('change', update_inputs)

            document.addEventListener('readystatechange', update_inputs)

        return JS(change_event, dict(id=self._id, max_choices=self.max))


class MDCLinearProgress(html.Div):
    def __init__(self):
        super().__init__(
            html.Div(
                html.Div(cls='mdc-linear-progress__buffer-bar'),
                cls='mdc-linear-progress__buffer'),
            html.Div(
                html.Span(cls='mdc-linear-progress__bar-inner'),
                cls='mdc-linear-progress__bar mdc-linear-progress__primary-bar'),
            html.Div(
                html.Span(cls='mdc-linear-progress__bar-inner'),
                cls='mdc-linear-progress__bar mdc-linear-progress__secondary-bar'),
            role='progressbar',
            cls='mdc-linear-progress',
            **{
                'data-mdc-auto-init': 'MDCLinearProgress',
                'aria-label': 'progress bar',
                'aria-valuemin': 0,
                'aria-valuemax': 1,
            }
        )
