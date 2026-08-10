from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalogos.models import (
    Categoria,
    Dependencia,
    EstatusPlaza,
    FuenteFinanciamiento,
    NivelEstructura,
    Programa,
    Proyecto,
    TipoContratacion,
    UnidadAdministrativa,
)
from servidores.models import InformacionBasica, Puesto, ServidorPublico, sincronizar_puesto


class EstadisticasViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester', password='secret123', rol='administrador'
        )

        self.estatus_ocupada = EstatusPlaza.objects.create(clave='O', descripcion='Ocupada')
        self.estatus_vacante = EstatusPlaza.objects.create(clave='V', descripcion='Vacante')

        self.dependencia = Dependencia.objects.create(clave='D01', descripcion='Dependencia test')
        self.unidad = UnidadAdministrativa.objects.create(
            dependencia=self.dependencia, clave='U01', descripcion='Unidad test'
        )
        self.programa = Programa.objects.create(
            dependencia=self.dependencia, unidad=self.unidad, clave='P01', descripcion='Programa test'
        )
        self.proyecto = Proyecto.objects.create(
            dependencia=self.dependencia, clave='PR01', descripcion='Proyecto test'
        )
        self.proyecto.programas.add(self.programa)

        self.categoria = Categoria.objects.create(clave='C01', descripcion='Categoría test')
        self.tipo_contratacion = TipoContratacion.objects.create(clave='TC1', descripcion='Contrato test')
        self.nivel_estructura = NivelEstructura.objects.create(clave='N01', descripcion='Nivel test', nivel=1)
        self.fuente_financiamiento = FuenteFinanciamiento.objects.create(clave='F01', descripcion='Fuente test')

        self.servidor = ServidorPublico.objects.create(
            expediente='EXP001',
            rfc='RFC0010001',
            curp='CURP00100010001',
            nombre='Nombre',
            primer_apellido='Apellido',
            fecha_nacimiento='1990-01-01',
            sexo='MASCULINO',
        )

        InformacionBasica.objects.create(
            fuente_financiamiento=self.fuente_financiamiento,
            dependencia=self.dependencia,
            unidad=self.unidad,
            programa=self.programa,
            proyecto=self.proyecto,
            id_plaza='PL001',
            categoria=self.categoria,
            puesto='Puesto test',
            nombramiento=self.tipo_contratacion,
            nivel_estructura=self.nivel_estructura,
            estatus_plaza=self.estatus_ocupada,
            servidor=self.servidor,
            quincena='2026-01',
            activo=True,
        )

        Puesto.objects.create(
            proyecto=self.proyecto,
            programa=self.programa,
            id_plaza='PL002',
            categoria=self.categoria,
            estatus_plaza=self.estatus_vacante,
        )

    def test_reporte_incluye_vacantes_en_estadisticas_por_estatus(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporte_estadisticas'))

        self.assertEqual(response.status_code, 200)
        por_estatus = response.context['stats']['por_estatus']
        labels = [item['estatus_plaza__descripcion'] for item in por_estatus]

        self.assertIn('Ocupada', labels)
        self.assertIn('Vacante', labels)

    def test_sincronizar_puesto_alinea_estatus_con_trabajador_asignado(self):
        puesto = Puesto.objects.create(
            proyecto=self.proyecto,
            programa=self.programa,
            id_plaza='PL003',
            categoria=self.categoria,
            estatus_plaza=self.estatus_vacante,
        )

        sincronizar_puesto(
            self.proyecto,
            self.programa,
            'PL003',
            self.categoria,
            self.servidor,
            unidad=self.unidad,
            nombramiento=self.tipo_contratacion,
            nivel_estructura=self.nivel_estructura,
            estatus_plaza=self.estatus_ocupada,
            cct=None,
            hsm=None,
            total_percepciones=0,
            total_bonos=0,
            total_neto=0,
            dias_pagados=0,
            id_plaza_jefe='',
        )

        puesto.refresh_from_db()
        self.assertEqual(puesto.estatus_plaza, self.estatus_ocupada)
        self.assertEqual(puesto.servidor_actual, self.servidor)

    def test_sincronizar_puesto_corrige_estatus_cuando_no_hay_cambios_de_datos(self):
        puesto = Puesto.objects.create(
            proyecto=self.proyecto,
            programa=self.programa,
            id_plaza='PL004',
            categoria=self.categoria,
            servidor_actual=self.servidor,
            estatus_plaza=self.estatus_vacante,
        )

        sincronizar_puesto(
            self.proyecto,
            self.programa,
            'PL004',
            self.categoria,
            self.servidor,
            unidad=self.unidad,
            nombramiento=self.tipo_contratacion,
            nivel_estructura=self.nivel_estructura,
            estatus_plaza=self.estatus_ocupada,
            cct=None,
            hsm=None,
            total_percepciones=0,
            total_bonos=0,
            total_neto=0,
            dias_pagados=0,
            id_plaza_jefe='',
        )

        puesto.refresh_from_db()
        self.assertEqual(puesto.estatus_plaza, self.estatus_ocupada)
