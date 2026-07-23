# Glosario diagnóstico de ERGONEKTIM

**Idioma:** Español  
**Contraparte semántica:** [`GLOSSARY.md`](GLOSSARY.md)  
**Alcance:** Observaciones, coordenadas de estado, métricas de evidencia, configuración y señales diagnósticas del producto  
**Estatus:** Glosario fundacional

## Cómo leer este glosario

ERGONEKTIM distingue cuatro roles:

| Rol | Significado |
|---|---|
| **Entrada** | Valor suministrado por una fuente o adaptador de dominio declarado |
| **Estado** | Coordenada causal producida por el kernel certificado |
| **Evidencia** | Valor derivado que un observador emplea para justificar un diagnóstico |
| **Configuración** | Valor congelado antes de evaluar; no es por sí mismo un resultado |

Salvo que el contrato de fuente declare unidades físicas, las coordenadas del kernel están normalizadas y son adimensionales. Una etiqueta diagnóstica nunca sustituye los valores de evidencia que la justifican.

## 1. Tiempo e identidad del registro

| Símbolo o campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `t` | Entrada | Timestamp causal de una observación, representado canónicamente en UTC. |
| `k` | Entrada | Posición base cero de una entrada aceptada en el flujo emitido. |
| `h` | Configuración | Duración de un paso de estado, expresada en bins del flujo. Las corridas eléctricas horarias normalmente declaran `h=1 h`. |
| `input_index` | Estado | Índice de la entrada consumida para producir la fila actual. |
| `state_index` | Estado | Índice del estado resultante; `state_index = input_index + 1`. |
| `valid` | Estado | Confirma que la fila se emitió bajo el contrato de entrada. Una fila interna inválida falla cerrada y no se emite como estado válido. |

## 2. Observación y estado universal

| Símbolo o campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `omega`, `ω` | Entrada | Cantidad de dominio observada después del adaptador eléctrico y normalización declarados. |
| `expected`, `ω_hat` | Entrada | Expectativa causal disponible no después de `t`; no debe utilizar observaciones futuras. |
| `sigma_op`, `σ_op` | Entrada | Máscara booleana de elegibilidad operacional. `false` significa que el estado no es elegible para diagnóstico operacional en esa fila. |
| `delta`, `Δ` | Evidencia | Discrepancia instantánea normalizada: `abs(ω-ω_hat)/(ω_hat+1)`. Mide desacople, no severidad de falla. |
| `delta_ref` | Configuración | Referencia positiva de calibración que hace comparables las discrepancias sin leer outcomes de evaluación. |
| `delta_tilde`, `Δ_tilde` | Evidencia | Discrepancia escalada por referencia: `Δ/delta_ref`. |
| `tau`, `τ` | Configuración | Escala de memoria causal en bins emitidos. Gobierna la retención, pero no es un resultado diagnóstico. |
| `r` | Configuración | Factor exacto de retención `exp(-h/τ)`. Es derivado y nunca se ajusta independientemente. |
| `xi`, `Ξ` | Estado | Tensión estructural acumulada causalmente. `Ξ_next = r Ξ + (1-r) Δ_tilde`. Valores mayores significan más desacople retenido, no una falla futura automática. |
| `theta`, `Θ` | Estado | Umbral endógeno de viabilidad inducido por la capacidad remanente: `Θ = theta_scale * λ`. |
| `lambda`, `λ` | Estado | Capacidad o permisividad remanente acotada para absorber tensión acumulada. |
| `e` | Estado | Exceso positivo anterior a la actualización: `max(Ξ-Θ,0)`. Es la cantidad añadida a la deuda acumulada. |
| `A` | Estado | Deuda monótona de exceso acumulado. Registra exceso pasado no resuelto y no se reinicia por una entrada temporal de recuperación. |
| `u_lambda`, `u_λ` | Entrada | Entrada no negativa declarada de regeneración o restauración de capacidad. Debe proceder del contrato de dominio. |
| `pi`, `π` | Evidencia | Impulso de clip en la frontera de capacidad: diferencia entre capacidad acotada y capacidad cruda. Registra el efecto aritmético de los límites declarados. |
| `M` | Estado | Margen de viabilidad `Θ-Ξ`. Margen positivo significa tensión bajo el umbral actual; margen negativo significa que el umbral fue excedido. |
| `smooth_M` | Evidencia | Media aritmética causal móvil de `M` sobre la ventana declarada de filas emitidas. |
| `G` | Evidencia | Cambio hacia atrás de `smooth_M`. `G` negativo significa deterioro de la tendencia causal del margen; `G` positivo significa mejoría. |

## 3. Configuración congelada del kernel

| Campo | Rol | Definición |
|---|---|---|
| `theta_scale` | Configuración | Escala positiva que convierte `λ` en `Θ`. |
| `lambda_0` | Configuración | Capacidad inicial dentro del intervalo declarado. |
| `lambda_min` | Configuración | Piso de capacidad. Alcanzarlo no elimina deuda ni tensión. |
| `lambda_max` | Configuración | Techo de capacidad. |
| `kappa_v3`, `κ` | Configuración | Acoplamiento de la deuda acumulada con el drenaje de capacidad. |
| `g_smooth` | Configuración | Número de márgenes emitidos usados por la media móvil causal. |

## 4. Telemetric Status y observabilidad

| Símbolo o campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `q` | Entrada | Drenaje observado normalizado usado por la envolvente telemétrica del estado de reserva. Su normalización se declara en el contrato de fuente. |
| `source_valid` | Entrada | Validez de una fuente individual en el timestamp actual. |
| `joint_source_valid` | Evidencia | Conjunción lógica de todas las fuentes requeridas por el observador. |
| `s_lower`, `s_minus` | Estado | Cota causal inferior del estado de reserva admisible después de observaciones ausentes. |
| `s_upper`, `s_plus` | Estado | Cota causal superior del estado de reserva admisible. |
| `interval_width` | Evidencia | `s_upper-s_lower`; incertidumbre inducida por ausencia de datos y memoria retenida. |
| `g_per_step` | Configuración | Coeficiente de contracción o regeneración del intervalo telemétrico. Es distinto de la tendencia de margen `G`. |
| `eta` | Configuración | Coeficiente máximo de drenaje por fila ausente bajo el contrato congelado del intervalo. |
| `q_max` | Configuración | Máximo drenaje normalizado admisible usado para propagación causal de peor caso. |
| `tol_s` | Configuración | Máximo ancho de intervalo compatible con observación clara. Se fija independientemente de la supervivencia de outcomes. |
| `observability_clear` | Evidencia | Gate booleano: los valores de fuente son válidos y el ancho causal no supera `tol_s`. |
| `quarantine_reasons` | Evidencia | Razones explícitas por las que un timestamp no puede sostener diagnósticos posteriores. |

## 5. Portador eléctrico con grafo

Estos campos aparecen únicamente cuando una evaluación declara una fuente de grafo físico.

| Símbolo o campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `v` | Entrada | Subestación representada como nodo del grafo primal. |
| `edge`, `e_graph` | Entrada | Circuito de transmisión identificado individualmente y representado como arista primal. |
| `boundary_node` | Entrada | Extremo de interconexión con estado parcial porque no es una subestación anfitriona completamente observada. |
| `c_v` | Entrada | Indicador booleano de que un outage automático nodal o de circuito incidente compromete al nodo `v`. |
| `z_v` | Estado | Envolvente ataque-liberación del compromiso: latch instantáneo ante evento y recuperación exponencial posterior. Es estado, no intensidad del evento. |
| `T_r` | Configuración | Tiempo de recuperación usado por la liberación de `z_v`, seleccionado mediante la regla preregistrada de calibración. |
| `edge_state` | Entrada | `conducting` o `isolated`, derivado de intervalos observados de outage de línea. |
| `planned` | Entrada | Intervención planificada declarada. Es una política exógena de aislamiento observada, no una falla inferida. |
| `active_subgraph` | Evidencia | Nodos y aristas conductoras disponibles en `t`. Representa conectividad observada, no flujo de potencia medido. |
| `E_z` | Evidencia | Energía de incompatibilidad de gluing a través de aristas conductoras. Las aristas aisladas no aportan término de acoplamiento. |
| `conducting_fraction` | Evidencia | Fracción de aristas físicas elegibles que se encuentran conductoras. |

## 6. Desplazamiento externo y Causal Link

| Símbolo o campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `w_j(t)` | Entrada | Componente de desplazamiento externo con observación, referencia causal, normalización firmada o absoluta declarada, validez y procedencia propias. Los componentes no se agrupan por defecto. |
| `w_valid` | Evidencia | Máscara de elegibilidad de cada componente externo. Los valores inválidos quedan en cuarentena y no se imputan. |
| `Phi`, `Φ` | Entrada | Registro interno u organizacional declarado y ofrecido a la comparación de atribución. Causal Link permanece fail-closed hasta validar contractualmente su fuente, construcción causal, gate de validez, independencia de outcomes y puente A0-a-E1–E5. |
| `Psi_j`, `Ψ_j` | Evidencia | Brazo de respuesta externa asociado al componente `j`. |
| `mismatch` | Evidencia | Discrepancia local `abs(Φ-Ψ_j)`. |
| `mismatch_change` | Evidencia | Cambio de la discrepancia respecto de la fila elegible anterior. Valores no positivos significan ausencia de deterioro nuevo bajo este contrato local. |
| `phi_contribution` | Evidencia | Contribución Shapley simétrica de dos entradas asignada al cambio de `Φ`. |
| `psi_contribution` | Evidencia | Contribución Shapley simétrica de dos entradas asignada al cambio de `Ψ_j`. |
| `external_cause_labels` | Entrada | Etiquetas independientes de validación. Evalúan la atribución, pero nunca entran en su cálculo. |

Las etiquetas de Causal Link identifican la contribución de señal dominante. No demuestran por sí mismas causalidad física completa.

## 7. Representación del operador y Estimation Fidelity

| Símbolo o campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `R(t)` | Entrada | Representación externa y propiedad del operador del exceso estructural, emitida no después de `t` y normalizada bajo contrato declarado. |
| `structural_excess` | Evidencia | Exceso del kernel `Ξ-Θ`. |
| `representation_error` | Evidencia | Diferencia absoluta `abs(R-(Ξ-Θ))`. |
| `fidelity`, `F` | Evidencia | Fidelidad normalizada `1-representation_error/Θ`. Valores positivos indican error menor al umbral; cero es la frontera crítica; valores negativos indican error mayor al umbral. |
| `R_valid` | Evidencia | Elegibilidad por fila de la representación externa del operador. |

La fidelidad mide concordancia con una representación externa declarada. No establece que alguna de las dos representaciones sea la verdad física completa.

## 8. Evidencia de Performance Status

| Campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `structural_drain` | Evidencia | Término del libro mayor de drenaje de capacidad `κ h A`. |
| `regeneration` | Evidencia | Término del libro mayor de regeneración `h u_lambda`. |
| `net_solvency` | Evidencia | `regeneration-structural_drain`. Positivo indica predominio de regeneración; negativo indica predominio de drenaje. |
| `effective_flow` | Entrada | Cantidad de servicio o rendimiento eléctrico declarada por separado. Nunca se infiere desde `M`. |
| `flow_change` | Evidencia | Diferencia hacia atrás de `effective_flow`. |
| `margin_change` | Evidencia | Diferencia hacia atrás de `M`. |
| `regeneration_to_drain_ratio` | Evidencia | `regeneration/structural_drain` cuando el drenaje es positivo. Es indefinida cuando el denominador es cero. |
| `overoptimization_guard` | Evidencia | Dispara cuando el flujo efectivo aumenta mientras el margen de viabilidad disminuye. Es una señal anti-sobreoptimización, no una orden de despacho. |

## 9. Evidencia de Condition Report

| Campo | Rol | Definición y uso diagnóstico |
|---|---|---|
| `planned_episode` | Entrada | Intervalo contiguo máximo marcado como intervención planificada. |
| `pre_margin_median` | Evidencia | Mediana del margen en la ventana declarada anterior al episodio. |
| `during_margin_minimum` | Evidencia | Margen mínimo durante el episodio planificado. |
| `post_margin_median` | Evidencia | Mediana del margen en la ventana declarada de recuperación posterior. |
| `invested_drain` | Evidencia | `max(pre_margin_median-during_margin_minimum,0)`. |
| `restored_margin` | Evidencia | `post_margin_median-during_margin_minimum`. |
| `net_margin_vs_pre` | Evidencia | `post_margin_median-pre_margin_median`; determina la clasificación regenerativa, neutra o no restitutiva. |
| `restoration_per_invested_drain` | Evidencia | `restored_margin/invested_drain` cuando el drenaje invertido es positivo. |

## 10. Diccionario de estados diagnósticos

| Observador | Código canónico | Etiqueta de usuario | Lectura científica |
|---|---|---|---|
| Telemetric Status | `observability_clear` | Observación confiable | La observación y el gate de memoria causal están despejados. |
| Telemetric Status | `partially_observable_fail_closed` | Cobertura parcial | Algunos intervalos son elegibles y otros permanecen en cuarentena. |
| Telemetric Status | `instrument_indeterminate` | Visibilidad insuficiente | La evidencia no permite inferencia posterior de estado. |
| Stability Status | `viable` | Margen viable | `σ_op=1`, `M>=0` y `G>=0`. No es un teorema de estabilidad global. |
| Stability Status | `viable_with_negative_gradient` | Margen viable con gradiente negativo | `σ_op=1`, `M>=0` y `G<0`. Es una lectura basada solo en el signo, sin umbral de magnitud o persistencia; no es una alarma de colapso. |
| Stability Status | `collapsing` | Viabilidad comprometida | `M<0` o la máscara operacional declarada está inactiva en una fila observable. |
| Performance Status | `solvent` | Regeneración dominante | La regeneración supera el drenaje estructural. |
| Performance Status | `balanced` | Balance neutro | Regeneración y drenaje estructural son iguales. |
| Performance Status | `structural_ledger_inactive` | Libro mayor estructural inactivo | Regeneración y drenaje estructural son ambos cero. Informa cobertura de rama, no evidencia de balance. |
| Performance Status | `insolvent` | Drenaje dominante | El drenaje estructural supera la regeneración. |
| Performance Status | `overoptimization_guard_triggered` | Alerta de sobreoptimización | El flujo efectivo aumentó mientras el margen de viabilidad disminuyó. |
| Condition Report | `regenerative` | Intervención regenerativa | La mediana posterior supera su valor anterior al episodio. |
| Condition Report | `neutral_restitution` | Restitución neutra | Las medianas posterior y anterior son iguales. |
| Condition Report | `non_restitutive` | Recuperación insuficiente | La mediana posterior permanece por debajo de la mediana anterior. |
| Causal Link | `no_new_deterioration` | Sin deterioro nuevo | La discrepancia local no aumentó. |
| Causal Link | `phi_internal` | Señal interna dominante | La contribución de `Φ` al aumento de discrepancia es mayor. |
| Causal Link | `psi_environmental` | Señal ambiental dominante | La contribución externa `Ψ_j` es mayor. |
| Causal Link | `joint` | Contribución conjunta | Ambas contribuciones son iguales dentro de la tolerancia declarada. |
| Estimation Fidelity | `faithful_self_image` | Representación alineada | La fidelidad normalizada es positiva. |
| Estimation Fidelity | `critical_self_image` | Representación en límite crítico | La fidelidad es cero dentro de la tolerancia numérica. |
| Estimation Fidelity | `epistemically_saturated` | Desacople de representación | El error de representación supera `Θ`. |
| Cualquier observador | `instrument_indeterminate` | Evidencia insuficiente | El observador no es elegible y no emite afirmación sustantiva de estado. |

## 11. Lo que las señales no significan

- Favorable no significa libre de riesgo.
- Atención no predice un outage futuro.
- Crítico no identifica una causa física única.
- Indeterminado no es favorable ni desfavorable; es una negativa a inferir.
- Un brazo dominante de Causal Link no prueba por sí mismo causalidad física completa.
- Ninguna salida constituye una instrucción automática de despacho, switching o protección.
