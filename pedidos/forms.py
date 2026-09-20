from django import forms

from pedidos.models import Pedido


class FormPedido(forms.ModelForm):
    RECOGER = "recoger"
    ENVIAR = "enviar"
    ENTREGAS = [
        (RECOGER, "Paso a recogerlo al taller"),
        (ENVIAR, "Quiero que me lo envíen"),
    ]

    entrega = forms.ChoiceField(
        choices=ENTREGAS,
        initial=RECOGER,
        widget=forms.RadioSelect,
        label="¿Cómo lo recibís?",
    )

    class Meta:
        model = Pedido
        fields = ("nombre", "telefono", "email", "ciudad", "direccion", "vehiculo", "notas")
        labels = {
            "nombre": "Tu nombre",
            "telefono": "WhatsApp",
            "email": "Correo (opcional)",
            "ciudad": "Ciudad",
            "direccion": "Dirección",
            "vehiculo": "Tu vehículo (opcional)",
            "notas": "¿Algo que debamos saber?",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej. Andrés Gómez", "autocomplete": "name"}),
            "telefono": forms.TextInput(attrs={"placeholder": "311 262 9406", "inputmode": "tel", "autocomplete": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "andres@correo.com", "autocomplete": "email"}),
            "ciudad": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "direccion": forms.TextInput(attrs={"placeholder": "Cra. 00 #00-00, barrio"}),
            "vehiculo": forms.TextInput(attrs={"placeholder": "Ej. Toyota Hilux 2022"}),
            "notas": forms.Textarea(attrs={"rows": 3, "placeholder": "Ej. Necesito instalación el sábado."}),
        }

    def clean_telefono(self):
        # Se guarda como lo escribió el cliente, pero tiene que tener los
        # dígitos de un celular colombiano o el WhatsApp de vuelta no existe.
        crudo = self.cleaned_data["telefono"]
        digitos = "".join(c for c in crudo if c.isdigit())
        if len(digitos) < 10:
            raise forms.ValidationError(
                "Escribí el número completo, con los 10 dígitos del celular."
            )
        return crudo

    def clean(self):
        datos = super().clean()
        if datos.get("entrega") == self.ENVIAR and not datos.get("direccion", "").strip():
            self.add_error("direccion", "Necesitamos la dirección para poder enviártelo.")
        if datos.get("entrega") == self.RECOGER:
            datos["direccion"] = ""
        return datos
