# Constitución identitaria de ERGONEKTIM

**Expansión oficial:** *Evaluación Aptadinámica de la Viabilidad de Sistemas Eléctricos de Potencia*  
**Estatus del documento:** Fundacional  
**Idioma:** Español  
**Contraparte semántica:** [`IDENTITY.md`](IDENTITY.md)  
**Fecha de constitución:** 2026-07-21

## 1. Identidad

ERGONEKTIM es un producto diagnóstico auditable para la evaluación aptadinámica de sistemas eléctricos de potencia. Convierte observaciones causales y fechadas en señales explícitas y científicamente trazables de viabilidad, preservando la incertidumbre, la procedencia y los límites de inferencia.

ERGONEKTIM no es una teoría matemática independiente, un nuevo kernel universal, un simulador de flujo de potencia, un sistema de gestión de energía ni un sistema de control del operador.

## 2. Misión

ERGONEKTIM existe para hacer utilizable la evaluación de viabilidad estructural sin debilitar su disciplina científica. Evalúa:

1. integridad y suficiencia de la observación;
2. viabilidad y deterioro estructural;
3. desempeño de regeneración frente a drenaje;
4. condición antes y después de intervenciones planificadas;
5. señales de desplazamiento con predominio interno o ambiental; y
6. fidelidad entre el estado inducido y una representación propiedad del operador.

## 3. Dependencia normativa

ERGONEKTIM es una implementación del dominio eléctrico de la máquina de estados y los contratos universales de PRAMA Protokol. La dependencia es unidireccional:

```text
PRAMA Protokol  --->  ERGONEKTIM
```

ERGONEKTIM DEBE:

- consumir una versión declarada y certificada de PRAMA Protokol;
- conservar en cada corrida canónica la versión del kernel, el hash de recertificación, los hashes de implementación y la configuración;
- mantener los adaptadores eléctricos, contratos de fuente, máscaras y observadores fuera del kernel universal; y
- rechazar el mantenimiento de una copia interna divergente del kernel.

## 4. Objeto de evaluación

Un objeto de evaluación PUEDE ser una autoridad de balance, región eléctrica, red o subred identificable, población de activos o ventana operacional con cobertura declarada suficiente.

La completitud de la observación nunca se presume. La ausencia de datos, la cuarentena, los nodos frontera, la contaminación retardada de memoria y la validez de las fuentes forman parte del registro diagnóstico.

## 5. Salida diagnóstica

La salida primaria es un panel diagnóstico distributivo:

```text
Telemetric Status
Stability Status
Performance Status
Condition Report
Causal Link
Estimation Fidelity
```

Cada observador conserva su propia elegibilidad, procedencia, estados indeterminados, evidencia y límite de afirmación. ERGONEKTIM NO DEBE ocultar estados contradictorios de los observadores dentro de un escalar global o un único semáforo general.

## 6. Contrato de señal del producto

Cada evaluación emitida DEBE proporcionar dos capas inseparables:

1. una capa científica con el código canónico, valores, contratos, máscaras y evidencia; y
2. una capa de presentación con etiqueta accesible, severidad semántica, token de color, icono, explicación breve, resumen de evidencia, periodo de validez y acción de revisión sugerida.

El color NO DEBE ser el único portador de significado. Toda señal DEBE entenderse mediante texto e icono accesible. Una etiqueta de presentación NO DEBE ampliar la afirmación científica codificada por su estado canónico.

| Nivel | Token | Significado |
|---|---|---|
| Favorable | `favorable` | Condición compatible con la viabilidad declarada |
| Informativo | `informational` | Condición neutra o descriptiva |
| Atención | `attention` | Tendencia adversa que requiere revisión |
| Crítico | `critical` | Condición estructural comprometida |
| Indeterminado | `indeterminate` | Evidencia insuficiente; no se permite inferir estado |

## 7. Invariancia de presentación

Cambiar la presentación NO DEBE recalcular ni alterar una evaluación. Los
códigos canónicos, símbolos matemáticos, unidades, timestamps UTC, valores
numéricos, hashes y resultados científicos permanecen invariantes. Solo pueden
cambiar los textos de presentación y el formato regional.

## 8. Principios constitutivos

1. **Causalidad.** Ningún diagnóstico puede emplear información futura.
2. **Operación fail-closed.** La falta de cobertura, procedencia o contrato produce un estado indeterminado, no una conclusión imputada.
3. **Instrumento antes que outcome.** Las escalas, máscaras, gates y contratos se fijan antes de abrir resultados evaluativos.
4. **Referencias externas independientes.** El desplazamiento externo `w(t)` y la representación del operador `R(t)` no se reconstruyen desde las variables de estado de PRAMA.
5. **Sin simulación encubierta.** La conectividad observada no se presenta como flujo de potencia medido; las cantidades modeladas se declaran como modelos.
6. **Diagnóstico distributivo.** Los canales observadores no se agrupan en una puntuación global sin un contrato validado independiente.
7. **Custodia numérica.** Las corridas canónicas incorporan versión, hashes, configuración, recertificación y contratos.
8. **Preservación de resultados negativos.** Una ausencia válida de señal permanece como resultado y no se reinterpreta retrospectivamente como falla del instrumento.
9. **Separación de capas.** La dinámica universal pertenece a PRAMA Protokol; la realización eléctrica pertenece a ERGONEKTIM.
10. **Acoplamiento específico por autoridad.** Los componentes ambientales y operacionales se seleccionan de acuerdo con la envolvente física de cada autoridad, no mediante una plantilla genérica.

## 9. Límites de afirmación

ERGONEKTIM no afirma por defecto predecir apagones u outages futuros; prevenir fallas en cascada; establecer causalidad física completa; conocer el estado interno oculto del operador; reemplazar un EMS, análisis de contingencias, optimizador de despacho o sistema de protección; estimar flujo de potencia solo a partir de conectividad; establecer cumplimiento regulatorio; ni estar validado para control operacional en tiempo real.

Cualquiera de esas afirmaciones requiere un encargo independiente, preregistrado y respaldado por evidencia apropiada.

## 10. Frontera del repositorio

El repositorio del producto contiene únicamente hitos consolidados: adaptadores de fuentes eléctricas y contratos de observación; gates de cobertura y máscaras causales; observadores operacionales y mapeos de presentación; pruebas deterministas y artefactos canónicos; ejemplos sintéticos y evidencia autorizada; y documentación metodológica y de usuario.

Quedan excluidos los datos privados o no autorizados, credenciales, copias modificadas de PRAMA Protokol, barridos guiados por outcomes, intentos abandonados sin valor documental, material no relacionado del laboratorio y rutas locales absolutas.

## 11. Regla de publicación

Un hito solo puede publicarse cuando cuenta con contrato explícito, implementación reproducible, pruebas aprobadas, procedencia completa, límite de afirmación declarado, un único artefacto canónico verificable y documentación coherente con el código.

El laboratorio experimental conserva la historia exploratoria. ERGONEKTIM conserva el producto consolidado.

## Declaración canónica

> **ERGONEKTIM es un producto auditable de evaluación aptadinámica para sistemas eléctricos de potencia. Convierte observaciones causales en diagnósticos de viabilidad comprensibles, visualmente explícitos y científicamente trazables, preservando la incertidumbre, la procedencia y los límites de inferencia.**
