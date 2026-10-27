from django import forms
from django.core.exceptions import ValidationError
from inventario.models import Categoria, Producto


class CategoriaForm(forms.ModelForm):
    """
    Formulario para la creación y validación de categorías (HU-001)
    """

    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'id': 'id_nombre',
                'class': 'w-full py-2.5 px-3.5 text-sm rounded-lg border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 text-slate-800 placeholder-slate-400 transition-colors',
                'placeholder': 'Ej. Bebidas y Licores',
                'autocomplete': 'off',
            }),
            'descripcion': forms.Textarea(attrs={
                'id': 'id_descripcion',
                'class': 'w-full py-2.5 px-3.5 text-sm rounded-lg border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 text-slate-800 placeholder-slate-400 transition-colors',
                'rows': 3,
                'placeholder': 'Detalle opcional sobre los artículos que engloba la categoría...',
            }),
            'activo': forms.CheckboxInput(attrs={
                'id': 'id_activo',
                'class': 'w-4 h-4 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500 transition-colors',
            }),
        }

    def clean_nombre(self) -> str:
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre de la categoría es obligatorio.')

        if len(nombre) > 100:
            raise forms.ValidationError('El nombre no puede superar los 100 caracteres.')

        query = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError('La categoría ya se encuentra registrada')

        return nombre

    def clean_descripcion(self) -> str:
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        if len(descripcion) > 500:
            raise forms.ValidationError('La descripción no puede superar los 500 caracteres.')
        return descripcion


class ProductoForm(forms.ModelForm):
    """
    Formulario para la creación y validación de productos (HU-004)
    """
    precio_compra = forms.CharField(
        required=True,
        label="Precio Compra",
        widget=forms.TextInput(attrs={
            'id': 'id_precio_compra',
            'inputmode': 'numeric',
            'autocomplete': 'off',
            'placeholder': '0',
            'class': 'w-full py-2.5 pr-3.5 pl-1.5 text-sm font-mono tabular-nums bg-transparent text-on-surface placeholder-outline focus:outline-none',
        })
    )
    precio_venta = forms.CharField(
        required=True,
        label="Precio Venta",
        widget=forms.TextInput(attrs={
            'id': 'id_precio_venta',
            'inputmode': 'numeric',
            'autocomplete': 'off',
            'placeholder': '0',
            'class': 'w-full py-2.5 pr-3.5 pl-1.5 text-sm font-mono tabular-nums bg-transparent text-on-surface placeholder-outline focus:outline-none',
        })
    )

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'categoria',
            'precio_compra',
            'precio_venta',
            'stock_actual',
            'stock_minimo',
            'descripcion',
            'activo',
            'imagen',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'id': 'id_nombre',
                'class': 'w-full py-2.5 px-3.5 text-sm rounded-lg border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 text-slate-800 placeholder-slate-400 transition-colors',
                'placeholder': 'Ej. Coca Cola 1.5L',
                'autocomplete': 'off',
            }),
            'categoria': forms.Select(attrs={
                'id': 'id_categoria',
                'class': 'w-full py-2.5 px-3.5 text-sm rounded-lg border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 text-slate-800 bg-white transition-colors',
            }),
            'stock_actual': forms.NumberInput(attrs={
                'id': 'id_stock_actual',
                'step': '1',
                'min': '0',
                'class': 'w-full py-2.5 px-3.5 text-sm font-mono tabular-nums rounded-lg border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 text-slate-800 placeholder-slate-400 transition-colors',
                'placeholder': '0',
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'id': 'id_stock_minimo',
                'step': '1',
                'min': '0',
                'class': 'w-full py-2.5 px-3.5 text-sm font-mono tabular-nums rounded-lg border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 text-slate-800 placeholder-slate-400 transition-colors',
                'placeholder': '0',
            }),
            'descripcion': forms.Textarea(attrs={
                'id': 'id_descripcion',
                'rows': 3,
                'class': 'w-full py-2.5 px-3.5 text-sm rounded-lg border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20 text-slate-800 placeholder-slate-400 transition-colors',
                'placeholder': 'Detalle opcional sobre las especificaciones del artículo...',
            }),
            'activo': forms.CheckboxInput(attrs={
                'id': 'id_activo',
                'class': 'w-4 h-4 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500 transition-colors',
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'id': 'id_imagen',
                'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 transition-colors',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.filter(activo=True).order_by('nombre')
        self.fields['categoria'].empty_label = "Seleccione una categoría"
        if not self.instance or not self.instance.pk:
            self.fields['activo'].initial = True
        else:
            if self.instance.precio_compra is not None:
                int_compra = int(round(self.instance.precio_compra))
                self.initial['precio_compra'] = f"{int_compra:,}".replace(',', '.')
            if self.instance.precio_venta is not None:
                int_venta = int(round(self.instance.precio_venta))
                self.initial['precio_venta'] = f"{int_venta:,}".replace(',', '.')


    def clean_nombre(self) -> str:
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del producto es obligatorio.')

        if len(nombre) > 100:
            raise forms.ValidationError('El nombre no puede superar los 100 caracteres.')

        query = Producto.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError('El producto ya se encuentra registrado')

        return nombre

    def clean_precio_compra(self) -> Decimal:
        from decimal import Decimal
        raw_val = self.cleaned_data.get('precio_compra')
        if raw_val is None or str(raw_val).strip() == '':
            raise forms.ValidationError('El precio de compra es obligatorio.')

        val_str = str(raw_val).strip().replace('$', '').replace(' ', '')
        if val_str.endswith('.00'):
            val_str = val_str[:-3].replace('.', '')
        else:
            val_str = val_str.replace('.', '')

        if ',' in val_str:
            val_str = val_str.split(',')[0]

        try:
            precio = Decimal(val_str)
        except Exception:
            raise forms.ValidationError('Ingrese un precio de compra válido.')

        if precio < 0:
            raise forms.ValidationError('El precio de compra no puede ser negativo.')

        return precio

    def clean_precio_venta(self) -> Decimal:
        from decimal import Decimal
        raw_val = self.cleaned_data.get('precio_venta')
        if raw_val is None or str(raw_val).strip() == '':
            raise forms.ValidationError('El precio de venta es obligatorio.')

        val_str = str(raw_val).strip().replace('$', '').replace(' ', '')
        if val_str.endswith('.00'):
            val_str = val_str[:-3].replace('.', '')
        else:
            val_str = val_str.replace('.', '')

        if ',' in val_str:
            val_str = val_str.split(',')[0]

        try:
            precio = Decimal(val_str)
        except Exception:
            raise forms.ValidationError('Ingrese un precio de venta válido.')

        if precio < 0:
            raise forms.ValidationError('El precio de venta no puede ser negativo.')

        return precio


    def clean_stock_actual(self):
        stock = self.cleaned_data.get('stock_actual')
        if stock is not None and stock < 0:
            raise forms.ValidationError('El stock actual no puede ser negativo.')
        return stock

    def clean_stock_minimo(self):
        stock = self.cleaned_data.get('stock_minimo')
        if stock is not None and stock < 0:
            raise forms.ValidationError('El stock mínimo no puede ser negativo.')
        return stock

    def clean_descripcion(self) -> str:
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        if len(descripcion) > 500:
            raise forms.ValidationError('La descripción no puede superar los 500 caracteres.')
        return descripcion

