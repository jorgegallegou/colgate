from agent import preguntar

THREAD_ID = "test-persistencia-001"

print("Enviando pregunta de seguimiento...")
respuesta = preguntar("¿Y cuándo llegaron exactamente?", THREAD_ID)
print(f"Respuesta: {respuesta}")
print("Listo.")