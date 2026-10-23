# TagVerse: Evolución

Juego de **la lleva** en 3D dentro de una estación espacial. Quien tenga la lleva cuando el reloj llegue a cero pierde la ronda.

Se juega en el navegador, en PC o en el celular, sin instalar nada.

## Cómo jugar

1. Abre la página y escribe tu nombre.
2. En la pestaña **Personaje** elige color, accesorio de cabeza y de espalda.
3. Pulsa **Practicar con bots**. Apareces en la **sala de espera**: elige cuántos bots y cuánto dura la ronda, y pulsa **Empezar partida**.

### Controles

| | PC | Celular |
|---|---|---|
| Moverse | WASD o flechas | Joystick (toca la mitad izquierda) |
| Mirar | Arrastrar con el ratón | Arrastrar en la mitad derecha |
| Saltar | Espacio | Botón **Saltar** |
| Dash | Shift | Botón **Dash** |
| Primera / tercera persona | V | Botón **Vista** |

## Qué tiene

- **Estación Órbita**: 9 salas (Comedor, Puente de mando, Reactor, Motores, Laboratorio, Oxígeno, Seguridad, Almacén, Comunicaciones) unidas por pasillos, con cajas y plataformas para saltar.
- **Mutación de quien la lleva**: es más rápido pero gira peor.
- **Orbes de evolución**: Velocidad, Doble salto, Dash, Escudo, Teletransporte y Furia.
- **Director de juego (IA)**: si la partida se estanca, cierra compuertas, abre conductos de ventilación, invierte la gravedad del Laboratorio o provoca un apagón.
- **Bots** que se mueven por las salas, persiguen, huyen y recogen orbes.
- **Personajes 3D** modelados y animados en Blender: reposo, correr, salto, dash y celebración.
- Minimapa, marcador, pantalla de resultados y sala de espera con lista de jugadores.

## Multijugador

El multijugador en línea (crear sala, código, QR y chat) usa el servicio de salas de los artifacts de Claude, así que **solo funciona dentro de Claude**. En esta versión de GitHub se juega en modo práctica contra bots.

## Archivos

| Archivo | Qué es |
|---|---|
| `index.html` | El juego completo (HTML, CSS y JavaScript). |
| `runner.json` | El personaje en formato glTF, exportado desde Blender. |
| `station.json` | La estación en formato glTF, exportada desde Blender. |
| `lib/` | three.js r128 (motor 3D), GLTFLoader, SkeletonUtils y qrcode-generator, todos con licencia MIT. |
| `blender-src/` | Scripts de Python que generan el personaje y la estación en Blender. |

### Regenerar los modelos con Blender

```bash
cd blender-src
python3 layout.py                                                        # plano de la estación
blender -b -P build_station.py -- layout.json station.glb station.blend  # estación
blender -b -P build_char.py -- runner.glb runner.blend                   # personaje
```

El juego carga los modelos como `.json`, que es glTF con los datos incrustados. Para convertir un `.glb` a ese formato hay que pasar el bloque binario a una URI `data:` en base64.

## Probarlo en tu PC

Los modelos se cargan con `fetch`, así que hay que abrir el juego con un servidor local y no haciendo doble clic en el archivo:

```bash
python3 -m http.server 8000
# luego abre http://localhost:8000
```
