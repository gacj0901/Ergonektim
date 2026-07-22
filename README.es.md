# ERGONEKTIM

*Evaluación Aptadinámica de la Viabilidad de Sistemas Eléctricos de Potencia*

**Español** | [English](README.md)

ERGONEKTIM es un producto bilingüe y auditable que convierte observaciones eléctricas causales en diagnósticos de viabilidad explícitos, distributivos y científicamente trazables.

## Estatus actual

`0.1.0.dev0` — construcción ejecutable del contrato de producto. No se formula ninguna afirmación predictiva ni de operación en tiempo real.

El hito actual proporciona:

- la [constitución identitaria](IDENTIDAD.md);
- el [glosario diagnóstico](GLOSARIO.md);
- un contrato canónico de señales diagnósticas bilingües;
- catálogos de estados en inglés y español; y
- una ruta causal y fail-closed para ejecutar conjuntamente los seis observadores;
- una vinculación verificada por hash con PRAMA Protokol `0.3.0` y su artefacto de recertificación numérica; y
- pruebas ejecutables de paridad, libro mayor, compuertas e invariantes de atribución.

La máquina de estados universal procede de una versión certificada y declarada de PRAMA Protokol. ERGONEKTIM contiene la realización eléctrica y no mantiene una copia divergente del kernel.

Una evaluación canónica embebe la versión de PRAMA, el hash del kernel Python, el hash de la recertificación numérica y el resultado de cada verificación de vinculación. La cadena de versión por sí sola no es suficiente.

## Panel diagnóstico

ERGONEKTIM conserva por separado las salidas de seis observadores:

1. Telemetric Status;
2. Stability Status;
3. Performance Status;
4. Condition Report;
5. Causal Link; y
6. Estimation Fidelity.

No se emite un escalar global ni un semáforo general.

## Verificación en una corrida

Con el paquete certificado PRAMA Protokol `0.3.0` instalado, la fixture sintética completa se evalúa mediante:

```console
python examples/run_synthetic_assessment.py --recertification RUTA/A/v0_3_0_numeric_recertification.json --output assessment.json
```

El comando escribe un único artefacto JSON determinista que contiene la trayectoria de estado, las salidas de los seis observadores, ambas presentaciones lingüísticas, los contratos de fuente, los invariantes y la vinculación completa con la certificación del kernel. La fixture no contiene datos reales y sirve únicamente para verificación.

## Frontera de desarrollo

Aquí solo pertenecen hitos consolidados del producto. Los intentos experimentales, datos privados, rutas locales absolutas y ajustes guiados por outcomes permanecen fuera de este repositorio.
