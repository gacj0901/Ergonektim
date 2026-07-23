# ERGONEKTIM

*Evaluación Aptadinámica de la Viabilidad de Sistemas Eléctricos de Potencia*

**Español** | [English](README.md)

ERGONEKTIM es un producto bilingüe y auditable que convierte observaciones eléctricas causales en diagnósticos de viabilidad explícitos, distributivos y científicamente trazables.

## Estatus actual

`0.1.0.dev2` — construcción ejecutable del contrato de producto. No se formula ninguna afirmación predictiva ni de operación en tiempo real.

El hito actual proporciona:

- la [constitución identitaria](IDENTIDAD.md);
- el [glosario diagnóstico](GLOSARIO.md);
- un contrato canónico de señales diagnósticas bilingües;
- un [contrato universal y cerrado de entrada](INPUT_BUNDLE.es.md);
- catálogos de estados en inglés y español; y
- una ruta causal y fail-closed para ejecutar conjuntamente los seis observadores;
- un contrato explícito de custodia de `Phi` que mantiene Causal Link cerrado
  hasta validar el puente declarado A0-a-E1–E5;
- normalizaciones de desplazamiento externo firmada, absoluta relativa a la
  referencia y de escala fija, sin clipping ni agregación escalar;
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

Valide un paquete canónico y su vinculación certificada sin ejecutar la evaluación:

```console
ergonektim verify --bundle PAQUETE_ENTRADA --recertification RECERTIFICACION.json --language es
```

Ejecute la evaluación completa:

```console
ergonektim assess --bundle PAQUETE_ENTRADA --recertification RECERTIFICACION.json --output evaluacion.json --language es
```

El comando escribe un único artefacto JSON determinista que contiene la custodia de entrada, la trayectoria de estado, las salidas de los seis observadores, ambas presentaciones lingüísticas, los contratos de fuente, los invariantes y la vinculación completa con la certificación del kernel.

## Sala bilingüe de evaluación

El directorio [`dashboard`](dashboard/) contiene la sala de evaluación orientada al producto. Consume íntegramente en el navegador un artefacto `ergonektim.assessment.v1.1` ya terminado y proporciona:

- lecturas separadas de los seis observadores;
- custodia de entrada, kernel y recertificación;
- inspección de trayectoria estructural y evidencia;
- conmutación de presentación español/inglés; y
- filtrado por severidad sin recomputación científica.

El dashboard nunca transmite la evaluación abierta, recalcula estados de observador ni emite una puntuación general. Hay una versión privada desplegada en [ergonektim.gacj-xci.chatgpt.site](https://ergonektim.gacj-xci.chatgpt.site).

## Frontera de desarrollo

Aquí solo pertenecen hitos consolidados del producto. Los intentos experimentales, datos privados, rutas locales absolutas y ajustes guiados por outcomes permanecen fuera de este repositorio.
