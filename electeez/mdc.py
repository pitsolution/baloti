from django.middleware.csrf import get_token
from ryzom.components import components as html
from ryzom.py2js.decorator import JavaScript


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
    def __init__(self, text, icon=None):
        content = [html.Span(cls='mdc-button__ripple')]
        if icon:
            content.append(MDCIcon(icon))
        content.append(html.Span(text, cls='mdc-button__label'))
        super().__init__(
            *content,
            cls='mdc-button'
        )


class MDCButtonOutlined(html.Button):
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


class MDCButton(html.Button):
    def __init__(self, text, p=True, disabled=False):
        black = 'black-button' if p else ''
        attrs = {}
        if disabled:
            attrs['disabled'] = True
        super().__init__(
            html.Span(text, cls='mdc-button__label'),
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
    attrs = {'class': 'mdc-text-field__input'}

    def __init__(self, input_id='', label_id='', **kwargs):
        if not kwargs.get('name', None):
            self.attrs['name'] = input_id
        if not kwargs.get('type', None):
            kwargs['type'] = 'text'
        self.attrs['id'] = input_id
        self.attrs['aria-labelledby'] = label_id
        super().__init__(**self.attrs, **kwargs)


class MDCLabel(html.Span):
    def __init__(self, text, label_id=''):
        self.attrs = {
            'id': label_id,
            'class': 'mdc-floating-label'
        }
        super().__init__(text, **self.attrs)


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
    attrs = {'class': 'mdc-notched-outline'}

    def __init__(self, hint='', label_id=''):
        content = [
            html.Span(**{'class': 'mdc-notched-outline__leading'}),
            html.Span(
                MDCLabel(hint, label_id),
                **{'class': 'mdc-notched-outline__notch'}),
            html.Span(**{'class': 'mdc-notched-outline__trailing'}),
        ]
        super().__init__(*content, **self.attrs)


class MDCTextFieldHelperLine(html.Div):
    def __init__(self, text, role, **kwargs):
        super().__init__(
            html.Div(
                text,
                cls='mdc-text-field-helper-text mdc-text-field-helper-text--persitent mdc-text-field-helper-text--validation-msg',
                role=role,
            ),
            cls='mdc-text-field-helper-line',
            **kwargs
        )
        self.attrs['aria-hidden'] = 'true'


class MDCTextFieldOutlined(html.Div):
    def __init__(self, hint='', input_id='', label_id='', **kwargs):
        attrs = {'data-mdc-auto-init': 'MDCTextField'}
        name = kwargs.get('name', '')
        if not hint:
            hint = name
        if name and not input_id:
            input_id = name + '_input'
        if input_id and not label_id:
            label_id = input_id + '_label'
        super().__init__(
            html.Label(
                MDCNotchOutline(hint, label_id),
                MDCTextInput(input_id, label_id, **kwargs),
                cls='mdc-text-field mdc-text-field--outlined',
                **attrs
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
        super().__init__(
            html.Span(
                html.Span(cls='mdc-notched-outline__leading'),
                html.Span(cls='mdc-notched-outline__trailing'),
                cls='mdc-notched-outline'
            ),
            html.Span(
                html.Textarea(
                    value,
                    id=input_id,
                    cls='mdc-text-field__input',
                    **{'aria-label': 'Label'},
                    **kwargs),
                cls='mdc-text-field__resizer'),
            cls='mdc-text-field mdc-text-field--outlined mdc-text-field--textarea mdc-text-field--no-label',
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

        return JavaScript(change_event, dict(
            input_id=f'#{self.input_id}',
            label_id=self.selected_text._id,
        ))


class CSRFInput(html.Input):
    def __init__(self, view):
        super().__init__(
            type='hidden',
            name='csrfmiddlewaretoken',
            value=get_token(view.request)
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
        super().__init__(
            html.Span(cls='mdc-list-item__ripple'),
            html.Span(*content, cls='mdc-list-item__text'),
            cls='mdc-list-item'
        )


class MDCSnackBar(html.Div):
    def __init__(self, msg, status='success'):
        super().__init__(
            html.Div(
                html.Div(
                    msg,
                    cls='mdc-snackbar__label',
                    **{'aria-atomic': 'false'}
                ),
                html.Div(
                    html.Button(
                        html.Div(cls='mdc-button__ripple'),
                        html.Span('OK', cls='mdc-button__label'),
                        type='button',
                        cls='mdc-button mdc-snackbar__action'
                    ),
                    cls='mdc-snackbar__actions',
                    **{'aria-atomic': 'true'}
                ),
                cls='mdc-snackbar__surface',
                role='status',
                **{'aria-relevant': 'addition'}
            ),
            cls='mdc-snackbar',
            **{'data-mdc-auto-init': 'MDCSnackbar'}
        )

    def render_js(self):
        return (
            '\nvar snack = function() {' +
            '\n\tvar elem = document.querySelector(".mdc-snackbar");' +
            '\n\tsn = new mdc.snackbar.MDCSnackbar(elem);' +
            '\n\tsn.open();' +
            '\n}; '
        )
