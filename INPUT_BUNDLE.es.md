# Paquete universal de entrada

**Español** | [English](INPUT_BUNDLE.md)

Un paquete de entrada de ERGONEKTIM es un directorio inmutable que contiene exactamente dos archivos UTF-8:

```text
paquete/
├── manifest.json
└── timeseries.csv
```

El manifiesto usa el esquema `ergonektim.input-bundle.v1`. Su JSON Schema se empaqueta en `resources/schemas/input-bundle-manifest.schema.json`; el cargador ejecutable conserva la autoridad y aplica comprobaciones causales y entre campos adicionales.

## Contrato por roles

Los nombres de columna son locales. El manifiesto los vincula con estos roles obligatorios:

| Rol | Significado |
|---|---|
| `timestamp_column` | Timestamp ISO-8601 con offset explícito sobre una grilla completa, única y creciente. |
| `omega` | Magnitud operacional observada suministrada al canal de discrepancia de PRAMA. |
| `expected` | Magnitud esperada y causalmente disponible emparejada con `omega`. |
| `sigma_op` | Estado booleano de validez operacional. |
| `u_lambda` | Entrada no negativa de regeneración declarada para el libro mayor estructural. |
| `effective_flow` | Canal de flujo efectivo declarado para el guard de anti-sobreoptimización. |
| `planned` | Marcador booleano de mantenimiento o intervención planificada. |
| `q` | Drenaje telemétrico normalizado del intervalo causal de observabilidad. |
| `phi_register` | Registro interno de desajuste usado por Causal Link. |

La sección de telemetría declara una o más columnas de validez de fuente y el contrato completo del intervalo. La telemetría ausente o inválida jamás se imputa como observable.

## Desplazamiento externo \(w\)

`external_displacement.components` es una lista no vacía. Cada componente declara de manera independiente:

El registro \(w\) resultante se observa y se contrata para la atribución por componente de Enlace Causal. En el contrato actual del producto no está acoplado a la dinámica del kernel \((\Omega,\Xi,\mathcal{A},\lambda,\Theta,M,G)\). Los artefactos de evaluación exponen esta frontera de forma explícita; un acoplamiento futuro requiere un modelo preregistrado por separado.

- roles de observación y referencia;
- normalización y signo de estrés;
- sistema y propietario de la fuente;
- columnas de observación, referencia, validez y emisión de referencia; y
- independencia respecto del registro interno y el kernel PRAMA.

Los componentes nunca se fusionan en un escalar global. Una referencia emitida después del timestamp evaluado queda en cuarentena. La selección de componentes depende de la autoridad: el formato no prescribe demanda, viento, intercambio, hidrología, clima ni otro canal de dominio.

## Representación externa del operador \(R(t)\)

La representación del operador apunta a `structural_excess_xi_minus_theta`. Debe identificar propietario externo, acople operacional, normalización, unidades, validez y tiempo de emisión. Debe generarse independientemente de PRAMA y declarar una lista `prama_variables_used` vacía.

Causal Link no requiere etiquetas de evaluación. Las etiquetas independientes pueden utilizarse en un estudio de validación separado, pero la atribución operacional se calcula sin ellas.

## Regla de datos cerrados y custodia

La cabecera CSV debe coincidir exactamente con las columnas declaradas. Las columnas no declaradas —incluidos outcomes accidentales— detienen la carga. También detienen la carga los timestamps ingenuos, roles duplicados, archivos adicionales, escapes de ruta, configuraciones no finitas y contratos de fuente incompletos.

Cada resultado embebe:

- el manifiesto completo;
- SHA-256 de `manifest.json`;
- SHA-256 del CSV;
- SHA-256 separado por dominio del paquete completo;
- cobertura temporal y número de filas; y
- declaraciones explícitas de que no se accedió a roles de outcome ni columnas no declaradas.

No se embeben rutas locales absolutas.

## Línea de comandos

Valide el paquete y la vinculación certificada sin ejecutar la evaluación:

```console
ergonektim verify --bundle PAQUETE_ENTRADA --recertification RECERTIFICACION.json --language es
```

Ejecute una vez los seis observadores y escriba un artefacto bilingüe:

```console
ergonektim assess --bundle PAQUETE_ENTRADA --recertification RECERTIFICACION.json --output evaluacion.json --language es
```

Use `--language en` para mensajes terminales en inglés. El artefacto siempre embebe ambos idiomas y el conmutador no puede alterar los bytes científicos. Una salida existente nunca se reemplaza sin `--overwrite` explícito y no puede escribirse dentro del paquete inmutable.

El código de salida `0` significa terminación. El código `2` indica detención contractual fail-closed.
