---
trigger: always_on
---

# NFR-01: Especificación del Sistema de Diseño y Arquitectura UI/UX

- **ID:** `NFR-01-UI-UX`
- **Dominio:** Punto de Venta (POS) e Inventario - Tienda de Abarrotes
- **Stack Tecnológico UI:** Django Templates + Tailwind CSS + Vanilla JS / Alpine.js
- **Layout Maestro:** `inventario/templates/layouts/base.html` (o `authentication/templates/layouts/auth.html` para acceso)
- **Estado:** MANDATORIO / INMUTABLE

---

## 1. Propósito y Alcance
Este documento establece las restricciones no funcionales (NFR) de interfaz de usuario y experiencia de usuario para el sistema de gestión de ventas de abarrotes. Todo agente de código que genere, modifique o refactorice plantillas Django (`templates/`) **DEBE** cumplir estrictamente con estas especificaciones antes de dar por completada cualquier tarea.

---

## 2. Arquitectura del Layout Maestro

### 2.1. Uso Obligatorio de la Plantilla Base
1. **Punto único de entrada:** Toda vista principal debe extender de `{% extends "layouts/base.html" %}`.
2. **Prohibición de redeclaración estructural:** Ninguna plantilla secundaria puede incluir etiquetas `<html>`, `<head>`, `<body>`, `<aside>` (navegación global) ni `<header>` (barra superior global).
3. **Integración en Django Templates:** Utilizar los bloques definidos:
   - `{% block title %}{% endblock %}`: Título de la pestaña del navegador.
   - `{% block content %}{% endblock %}`: Contenedor principal de trabajo.
   - `{% block extra_css %}{% endblock %}` y `{% block extra_js %}{% endblock %}`: Estilos y scripts complementarios.

### 2.2. Regla de Inmutabilidad del Sidebar (Cero Desplazamiento)
El menú de navegación lateral opera exclusivamente bajo el patrón **Off-Canvas Overlay Drawer** en todas las resoluciones (`mobile`, `tablet`, `desktop`).

- **Estado Reactivo:** Controlado en el `<body>` mediante Alpine.js: `x-data="{ sidebarOpen: false }"` y `@keydown.window.escape="sidebarOpen = false"`.
- **Restricción de Flujo (No Content Push):**
  - El elemento `<main>` mantiene un ancho fluido e inmutable (`w-full max-w-7xl mx-auto`).
  - **ESTÁ ESTRICTAMENTE PROHIBIDO** añadir clases responsivas que empujen o redimensionen el contenido principal o fijar el sidebar en pantallas grandes (prohibido usar `lg:pl-72`, `md:ml-64`, `lg:static`, `lg:translate-x-0` o `lg:block` en el `<aside>` o `<main>`).
- **Opacado del Contenido (Backdrop):**
  - Cuando `sidebarOpen === true`, el área de trabajo principal debe opacarse mediante una capa fija superpuesta (`fixed inset-0 bg-slate-900/60 backdrop-blur-xs`) que captura el clic para cerrar el menú (`@click="sidebarOpen = false"`).

### 2.3. Jerarquía Estricta de Capas (`z-index`)
Para evitar colisiones visuales entre el menú superpuesto, la barra fija y los modales del POS, se debe respetar esta escala:

| Capa / Elemento | Clase Tailwind (`z-index`) | Comportamiento |
| :--- | :--- | :--- |
| Contenido Principal (`<main>`) | `z-0` / Flujo normal | Estático, nunca se desplaza horizontalmente. |
| Barra Superior (`<header>`) | `sticky top-0 z-30` | Siempre visible en la parte superior. |
| Backdrop del Sidebar | `fixed inset-0 z-40` | Opaca tanto el `<main>` como el `<header>`. |
| Sidebar Drawer (`<aside>`) | `fixed inset-y-0 left-0 z-50` | Se desliza sobre toda la interfaz (`w-72`). |
| Modales Operativos (Cobro, Alertas) | `fixed inset-0 z-60` | Superpuestos sobre cualquier otro elemento. |
| Notificaciones / Toasts | `fixed z-70` | Esquina superior o inferior derecha. |

---

## 3. Paleta de Colores y Tokens Semánticos ("Mercado Fresco POS")

La interfaz utiliza una combinación de alto contraste en navegación y superficies claras en el área de trabajo para reducir la fatiga visual del cajero. **Prohibido usar colores arbitrarios fuera de esta tabla.**

### 3.1. Superficies y Estructura
- **Canvas Principal (Fondo de página):** `bg-slate-50` (`#F8FAFC`)
- **Tarjetas, Tablas y Paneles:** `bg-white` (`#FFFFFF`) con borde `border border-slate-200` (`#E2E8F0`), radio `rounded-xl` y sombra `shadow-xs`.
- **Sidebar Lateral:** `bg-slate-900` (`#0F172A`) con cabecera/pie en `bg-slate-950/50` y divisores `border-slate-800`.
- **Header Superior:** `bg-white` con borde inferior `border-b border-slate-200`.

### 3.2. Colores de Acción y Estado Semántico
| Rol Semántico | Clases Base (Botones / Activos) | Clases de Badge / Alerta Suave | Uso Exclusivo en Dominio Abarrotes |
| :--- | :--- | :--- | :--- |
| **Primario (Éxito / Cobro)** | `bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-emerald-600` | `bg-emerald-50 text-emerald-700 border border-emerald-200` | Botón "Cobrar", guardar venta, confirmar ingreso de stock, ítem activo en el sidebar, estado "Caja Abierta". |
| **Secundario (Advertencia / Operación)** | `bg-amber-500 hover:bg-amber-600 text-white focus:ring-amber-500` | `bg-amber-50 text-amber-700 border border-amber-200` | Alertas de "Stock Bajo", corte parcial de caja, aplicar descuento manual, venta en espera / crédito (fiado). |
| **Peligro (Destructivo / Merma)** | `bg-rose-600 hover:bg-rose-700 text-white focus:ring-rose-600` | `bg-rose-50 text-rose-700 border border-rose-200` | Eliminar línea del ticket, anular venta, registrar producto vencido/merma, faltante en arqueo de caja. |
| **Neutro / Secundario UI** | `bg-white hover:bg-slate-50 text-slate-700 border border-slate-300` | `bg-slate-100 text-slate-700 border border-slate-200` | Cancelar modal, limpiar filtros, imprimir copia de recibo, acciones secundarias de tabla. |

---

## 4. Tipografía y Legibilidad de Datos

- **Fuente Principal (UI):** `Inter` (`font-sans`), renderizada con `antialiased`.
  - Títulos de sección: `text-lg font-bold text-slate-800 tracking-tight`.
  - Subtítulos de tarjetas: `text-base font-semibold text-slate-800`.
  - Texto de tabla y formularios: `text-sm text-slate-700`.
  - Etiquetas secundarias / ayudas: `text-xs text-slate-500`.
- **Fuente Monoespaciada (Datos Numéricos y Códigos):** `font-mono tabular-nums`.
  - **Regla obligatoria:** Todo código de barras (EAN-13/SKU), precio unitario, subtotal, cantidad en kardex y total a cobrar **DEBE** usar la clase `tabular-nums` (y `font-mono` en códigos) para garantizar la alineación vertical perfecta en tablas y tickets de venta.

---

## 5. Estándares de Componentes y Ergonomía POS

### 5.1. Inputs y Lector de Código de Barras
- Los campos de entrada deben tener altura cómoda para operación rápida: `py-2.5 px-3.5 text-sm rounded-lg border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20`.
- En la vista del Punto de Venta (POS), el input de búsqueda/escaneo de código de barras debe poseer el atributo `autofocus` y mantener el foco tras agregar un producto.

### 5.2. Accesibilidad por Teclado (Keyboard-First UX)
- Todo botón interactivo debe mostrar un anillo de foco visible (`focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-1`).
- Los modales y el *sidebar* deben cerrarse inmediatamente al presionar la tecla `Escape`.

### 5.3. Estados de Carga en Livewire
- Todo botón que dispare una transacción crítica (ej. `wire:click="procesarVenta"`) debe deshabilitarse durante la petición para evitar cobros duplicados:
  ```html
  <button wire:click="procesarVenta" wire:loading.attr="disabled" class="... disabled:opacity-50 disabled:cursor-not-allowed">
      <span wire:loading.remove wire:target="procesarVenta">Cobrar</span>
      <span wire:loading wire:target="procesarVenta">Procesando...</span>
  </button>
