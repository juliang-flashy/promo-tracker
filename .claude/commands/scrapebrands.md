# Skill: scrapebrands

Scrapea las marcas competidoras y extrae campañas, promociones y estrategias usando texto + análisis visual de screenshots.

## Instrucciones

### Paso 1 — Correr el scraper
```bash
set PYTHONIOENCODING=utf-8 && "C:\Users\ASUS\Documents\ambientes\inventario_pantalones\Scripts\python.exe" "C:\Users\ASUS\Desktop\competitive-intel\scraper\scrape_raw.py" $ARGUMENTS
```

### Paso 2 — Leer raw_scrape.json
Leer: `C:\Users\ASUS\Desktop\competitive-intel\data\raw_scrape.json`

### Paso 3 — Analizar CADA marca con texto + screenshot
Para cada marca con status "ok":
- Leer `texto_lineas` del JSON
- Leer el archivo de imagen en `screenshot` usando el Read tool (Claude tiene visión)
- Combinar ambas fuentes para extraer la información real

**IMPORTANTE:** El texto HTML pierde todo lo que está en imágenes y banners. El screenshot es la fuente de verdad para campañas y descuentos visuales. Siempre priorizar lo que se ve en el screenshot sobre el texto.

### Paso 4 — Extraer estos campos por marca

- **campana**: nombre exacto de la campaña visible en banners o texto
- **descuento**: porcentaje o monto exacto visible (ej: "60% OFF", "hasta 50%")
- **vigencia**: fechas exactas si aparecen
- **categorias_destacadas**: máximo 3 categorías en primer plano
- **beneficios**: envío gratis, cambios, cuotas, puntos — con montos exactos
- **collab**: colaboración con influencer o artista
- **tendencias**: máximo 3 tendencias de moda visibles
- **tono**: una palabra (aspiracional, divertido, minimalista, etc.)
- **urgencia**: frases de urgencia o escasez
- **canales**: canales de venta mencionados
- **precio_min / precio_max**: rango de precios visible
- **mensaje_principal**: frase o texto principal del banner

### Paso 5 — Guardar en promos.json
Guardar en: `C:\Users\ASUS\Desktop\competitive-intel\data\promos.json`

Formato por entrada:
```json
{
  "marca": "Flashy",
  "region": "nacional",
  "categoria": "moda",
  "url": "https://www.flashy.com.co/",
  "fecha": "2026-04-21",
  "campana": "La Veranita",
  "descuento": "60% OFF en referencias seleccionadas",
  "vigencia": null,
  "categorias_destacadas": ["camisetas", "blusas", "vestidos"],
  "beneficios": ["cambios gratis", "envío gratis desde $129.900", "pide ya y paga después", "gana puntos"],
  "collab": null,
  "tendencias": ["Made in Colombia", "oversize", "crop top"],
  "tono": "femenino empoderador",
  "urgencia": "aplican TyC",
  "canales": ["web", "WhatsApp", "tiendas físicas"],
  "precio_min": 59900,
  "precio_max": 154900,
  "mensaje_principal": "60% OFF en referencias seleccionadas — sección Rebajas"
}
```

### Paso 6 — Resumen final
Al terminar mostrar:
- Cuántas marcas procesadas
- Top 3 descuentos más agresivos
- Tendencias más repetidas
- Qué están haciendo las nacionales esta semana
