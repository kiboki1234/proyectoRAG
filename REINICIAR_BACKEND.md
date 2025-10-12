# 🔄 Reiniciar Backend para Aplicar Cambios

## Por Qué Siguen Apareciendo los Documentos

Aunque:
- ✅ Borraste `faiss.index`
- ✅ Borraste documentos de `docs/`
- ✅ El código de `app.py` está modificado

**El backend tiene los datos en memoria** y no se ha reiniciado.

---

## ✅ Solución: Reiniciar Backend

### En el Terminal "uvicorn"

```powershell
# 1. Detener el backend (presiona):
Ctrl + C

# 2. Esperar a que termine completamente

# 3. Reiniciar:
cd backend
python run_dev.py

# O si usas uvicorn directamente:
uvicorn app:app --reload --port 8000
```

---

## 🔍 Qué Pasará al Reiniciar

1. **Backend se detiene** → Libera memoria
2. **Backend inicia** → Carga nuevo código de `app.py`
3. **Endpoint `/sources`** → Solo lista archivos en `docs/`
4. **No hay `faiss.index`** → Se reconstruirá automáticamente (si tienes docs)
5. **Frontend lista documentos** → Solo verás los que existen ✅

---

## 📋 Pasos Exactos

**Paso 1**: Ve al terminal que dice "uvicorn" (donde corre el backend)

**Paso 2**: Presiona `Ctrl + C` y espera este mensaje:
```
INFO:     Shutting down
INFO:     Finished server process
```

**Paso 3**: Ejecuta:
```powershell
python run_dev.py
```

**Paso 4**: Espera a ver:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Paso 5**: Recarga el frontend (F5 en el navegador)

---

## 🎯 Verificación

Después de reiniciar:

1. **Abre DevTools** (F12)
2. **Ve a Network**
3. **Busca la request a `/sources`**
4. **Verifica la respuesta** - solo debe tener archivos de `docs/`

O simplemente:
- Abre el select de documentos en el frontend
- Debe mostrar **solo los archivos que existen en `docs/`** ✅

---

## ⚠️ Si Aún Aparecen

Si después de reiniciar TODAVÍA aparecen documentos borrados:

1. **Verifica qué archivos hay físicamente**:
   ```powershell
   cd backend\data\docs
   dir
   ```

2. **Verifica qué devuelve el endpoint**:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/sources" | ConvertFrom-Json
   ```

3. **Limpia caché del navegador**:
   - F12 → Network → Check "Disable cache"
   - Ctrl + Shift + R (hard refresh)

---

## 🔧 Comando Rápido

```powershell
# En el terminal uvicorn:
# 1. Ctrl+C (detener)
# 2. Ejecutar:
cd D:\proyectosPersonales\conferenciaSoftwareLibre\proyectoRAG\proyectoRAG\backend && python run_dev.py
```
