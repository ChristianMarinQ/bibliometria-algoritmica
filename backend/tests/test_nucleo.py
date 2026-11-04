"""Pruebas de nucleo/preprocesamiento.py, nucleo/vectorizacion.py y nucleo/corpus.py.

Cubre las funciones compartidas por todos los algoritmos del proyecto:
normalización, tokenización, limpieza, TF-IDF, operaciones sobre vectores
dispersos y estadísticas básicas del corpus.
"""

import math

import pytest

from app.nucleo.preprocesamiento import (
    STOPWORDS,
    frecuencias,
    limpiar_tokens,
    normalizar,
    preprocesar,
    tokenizar,
)
from app.nucleo.vectorizacion import (
    coseno_dispersos,
    frecuencia_inversa,
    frecuencia_termino,
    norma,
    producto_punto,
    tfidf,
)


# ============================================================
# nucleo/preprocesamiento — normalizar()
# ============================================================

class TestNormalizar:
    """La función normalizar pasa a minúsculas y sustituye ligaduras tipográficas."""

    def test_minusculas_basico(self):
        assert normalizar("Machine Learning") == "machine learning"

    def test_ligadura_fi(self):
        # La ligadura tipográfica ﬁ (U+FB01) debe convertirse en "fi"
        assert normalizar("ﬁeld") == "field"

    def test_ligadura_fl(self):
        assert normalizar("ﬂow") == "flow"

    def test_ligadura_ff(self):
        assert normalizar("eﬀect") == "effect"

    def test_ligaduras_multiples(self):
        # ﬁ y ﬂ en la misma cadena
        assert normalizar("ﬂuﬁd") == "flufid"

    def test_comillas_tipograficas(self):
        # Las comillas curvas deben normalizarse
        assert normalizar("\u2018hola\u2019") == "'hola'"
        assert normalizar("\u201chola\u201d") == '"hola"'

    def test_guion_largo(self):
        # Em dash y en dash → guion simple
        assert normalizar("state\u2013of\u2013the\u2014art") == "state-of-the-art"

    def test_cadena_ya_limpia(self):
        texto = "artificial intelligence in education"
        assert normalizar(texto) == texto

    def test_cadena_vacia(self):
        assert normalizar("") == ""


# ============================================================
# nucleo/preprocesamiento — tokenizar()
# ============================================================

class TestTokenizar:
    """tokenizar divide en palabras de solo letras a-z."""

    def test_palabras_simples(self):
        assert tokenizar("hello world") == ["hello", "world"]

    def test_separa_por_guion(self):
        # "problem-solving" → ["problem", "solving"]
        assert tokenizar("problem-solving") == ["problem", "solving"]

    def test_ignora_numeros_y_puntuacion(self):
        assert tokenizar("GPT-4: a model.") == ["gpt", "a", "model"]

    def test_cadena_vacia(self):
        assert tokenizar("") == []

    def test_solo_simbolos(self):
        assert tokenizar("123 !@# 456") == []

    def test_normaliza_mayusculas(self):
        # tokenizar llama internamente a normalizar
        assert tokenizar("Deep Learning") == ["deep", "learning"]

    def test_separadores_multiples(self):
        # Varios separadores consecutivos no producen tokens vacíos
        assert tokenizar("ai   ,  ml") == ["ai", "ml"]

    def test_ligadura_en_tokenizacion(self):
        # La ligadura ﬁ se normaliza antes de tokenizar
        assert tokenizar("ﬁeld research") == ["field", "research"]


# ============================================================
# nucleo/preprocesamiento — limpiar_tokens()
# ============================================================

class TestLimpiarTokens:
    """limpiar_tokens elimina stopwords y tokens demasiado cortos."""

    def test_elimina_stopwords(self):
        tokens = ["the", "model", "is", "good"]
        assert limpiar_tokens(tokens) == ["model", "good"]

    def test_elimina_tokens_cortos(self):
        # Tokens de 1 ó 2 letras que no son siglas conservadas se eliminan
        assert limpiar_tokens(["ai", "ml", "it"]) == ["ai"]  # solo "ai" está en SIGLAS_CONSERVADAS

    def test_conserva_sigla_ai(self):
        assert limpiar_tokens(["ai"]) == ["ai"]

    def test_longitud_minima_tres(self):
        # Exactamente 3 letras: se conserva
        assert limpiar_tokens(["cat"]) == ["cat"]
        # Exactamente 2 letras (no es sigla): se elimina
        assert limpiar_tokens(["ml"]) == []

    def test_lista_vacia(self):
        assert limpiar_tokens([]) == []

    def test_todos_son_stopwords(self):
        tokens = list(STOPWORDS)[:5]
        assert limpiar_tokens(tokens) == []

    def test_conserva_orden(self):
        tokens = ["learning", "models", "improve", "education"]
        resultado = limpiar_tokens(tokens)
        assert resultado == ["learning", "models", "improve", "education"]


# ============================================================
# nucleo/preprocesamiento — preprocesar()
# ============================================================

class TestPreprocesar:
    """preprocesar es el pipeline completo normalizar → tokenizar → limpiar."""

    def test_frase_tipica(self):
        resultado = preprocesar("Machine learning models improve education outcomes.")
        assert "machine" not in resultado  # "machine" tiene 7 letras y no es stopword → aparece
        assert "the" not in resultado
        assert "models" in resultado
        assert "education" in resultado
        assert "outcomes" in resultado

    def test_conserva_ai(self):
        resultado = preprocesar("AI is transforming education with AI tools.")
        assert resultado.count("ai") == 2

    def test_elimina_signos_de_puntuacion(self):
        resultado = preprocesar("Learning, analytics, and data.")
        assert "," not in " ".join(resultado)
        assert "." not in " ".join(resultado)

    def test_cadena_vacia(self):
        assert preprocesar("") == []

    def test_solo_stopwords(self):
        assert preprocesar("the and of in is it") == []

    def test_pipeline_completo_con_ligaduras(self):
        # La ligadura ﬁ debe desaparecer dentro del pipeline
        resultado = preprocesar("ﬁeld research methodology")
        assert "field" in resultado
        assert "research" in resultado


# ============================================================
# nucleo/preprocesamiento — frecuencias()
# ============================================================

class TestFrecuencias:
    """frecuencias cuenta apariciones de cada token."""

    def test_conteo_basico(self):
        conteo = frecuencias(["a", "b", "a", "c", "a"])
        assert conteo == {"a": 3, "b": 1, "c": 1}

    def test_lista_vacia(self):
        assert frecuencias([]) == {}

    def test_un_elemento(self):
        assert frecuencias(["learning"]) == {"learning": 1}

    def test_todos_distintos(self):
        tokens = ["ai", "ml", "nlp"]
        conteo = frecuencias(tokens)
        assert all(conteo[t] == 1 for t in tokens)

    def test_no_modifica_entrada(self):
        tokens = ["a", "b", "a"]
        copia = list(tokens)
        frecuencias(tokens)
        assert tokens == copia


# ============================================================
# nucleo/vectorizacion — frecuencia_termino()
# ============================================================

class TestFrecuenciaTermino:
    """TF normalizado: apariciones / total de tokens del documento."""

    def test_documento_un_token(self):
        tf = frecuencia_termino(["learning"])
        assert tf == {"learning": pytest.approx(1.0)}

    def test_documento_varios_tokens(self):
        tf = frecuencia_termino(["a", "b", "a"])
        assert tf["a"] == pytest.approx(2 / 3)
        assert tf["b"] == pytest.approx(1 / 3)

    def test_documento_vacio(self):
        tf = frecuencia_termino([])
        assert tf == {}

    def test_suma_igual_a_uno(self):
        tokens = ["ai", "learning", "model", "ai", "data"]
        tf = frecuencia_termino(tokens)
        assert sum(tf.values()) == pytest.approx(1.0)

    def test_todos_los_valores_entre_cero_y_uno(self):
        tokens = ["x", "y", "z", "x"]
        tf = frecuencia_termino(tokens)
        for valor in tf.values():
            assert 0.0 <= valor <= 1.0


# ============================================================
# nucleo/vectorizacion — frecuencia_inversa()
# ============================================================

class TestFrecuenciaInversa:
    """IDF suavizado: ln((1+N)/(1+df)) + 1."""

    def test_un_documento(self):
        # Con N=1 y df=1: ln((1+1)/(1+1)) + 1 = ln(1) + 1 = 1.0
        idf = frecuencia_inversa([["aprendizaje"]])
        assert idf["aprendizaje"] == pytest.approx(1.0)

    def test_termino_en_todos_los_docs(self):
        # Con N=3 y df=3: ln((1+3)/(1+3)) + 1 = 0 + 1 = 1.0
        docs = [["ai", "learning"], ["ai", "model"], ["ai", "data"]]
        idf = frecuencia_inversa(docs)
        assert idf["ai"] == pytest.approx(1.0)

    def test_termino_en_un_doc_de_tres(self):
        # Con N=3 y df=1: ln((1+3)/(1+1)) + 1 = ln(2) + 1 ≈ 1.693
        docs = [["raro"], ["otro"], ["mas"]]
        idf = frecuencia_inversa(docs)
        esperado = math.log(4 / 2) + 1
        assert idf["raro"] == pytest.approx(esperado)

    def test_idf_nunca_negativo(self):
        docs = [["a"], ["a"], ["a"], ["a"], ["a"]]
        idf = frecuencia_inversa(docs)
        for valor in idf.values():
            assert valor >= 0.0

    def test_termino_mas_raro_tiene_idf_mayor(self):
        # "raro" aparece en 1 doc, "comun" en 3 de 3
        docs = [["comun", "raro"], ["comun"], ["comun"]]
        idf = frecuencia_inversa(docs)
        assert idf["raro"] > idf["comun"]


# ============================================================
# nucleo/vectorizacion — tfidf()
# ============================================================

class TestTfidf:
    """tfidf devuelve vectores dispersos y el diccionario IDF."""

    def test_longitud_de_vectores(self):
        docs = [["a", "b"], ["b", "c"]]
        vectores, idf = tfidf(docs)
        assert len(vectores) == 2

    def test_termino_ausente_no_en_vector(self):
        docs = [["ai", "model"], ["data", "model"]]
        vectores, _ = tfidf(docs)
        # "data" no debe estar en el vector del primer documento
        assert "data" not in vectores[0]

    def test_pesos_no_negativos(self):
        docs = [["learning", "ai", "ai"], ["model", "ai"]]
        vectores, _ = tfidf(docs)
        for vector in vectores:
            for peso in vector.values():
                assert peso >= 0.0

    def test_idf_calculado_sobre_corpus(self):
        docs = [["a"], ["b"], ["c"]]
        _, idf = tfidf(docs)
        # Cada término aparece en 1 de 3 docs: ln(4/2)+1 = ln(2)+1
        esperado = math.log(2) + 1
        for t in ["a", "b", "c"]:
            assert idf[t] == pytest.approx(esperado)


# ============================================================
# nucleo/vectorizacion — producto_punto()
# ============================================================

class TestProductoPunto:
    """producto_punto sobre vectores dispersos (diccionarios)."""

    def test_sin_terminos_comunes(self):
        a = {"x": 1.0, "y": 2.0}
        b = {"z": 3.0}
        assert producto_punto(a, b) == 0.0

    def test_con_terminos_comunes(self):
        a = {"x": 2.0, "y": 3.0}
        b = {"x": 4.0, "y": 1.0}
        assert producto_punto(a, b) == pytest.approx(2 * 4 + 3 * 1)

    def test_simetria(self):
        a = {"ai": 0.5, "model": 0.3}
        b = {"model": 0.7, "data": 0.2}
        assert producto_punto(a, b) == pytest.approx(producto_punto(b, a))

    def test_vector_vacio(self):
        assert producto_punto({}, {"x": 1.0}) == 0.0
        assert producto_punto({}, {}) == 0.0

    def test_usa_el_mas_pequeno_primero(self):
        # El resultado debe ser correcto sin importar cuál es más pequeño
        a = {"x": 1.0}
        b = {"x": 2.0, "y": 3.0}
        assert producto_punto(a, b) == pytest.approx(2.0)
        assert producto_punto(b, a) == pytest.approx(2.0)


# ============================================================
# nucleo/vectorizacion — norma()
# ============================================================

class TestNorma:
    """norma euclidiana de un vector disperso."""

    def test_vector_unitario(self):
        assert norma({"x": 1.0}) == pytest.approx(1.0)

    def test_vector_pitagorico(self):
        # ‖(3, 4)‖ = 5
        assert norma({"a": 3.0, "b": 4.0}) == pytest.approx(5.0)

    def test_vector_vacio(self):
        assert norma({}) == pytest.approx(0.0)

    def test_valores_fraccionarios(self):
        v = {"x": 0.6, "y": 0.8}
        assert norma(v) == pytest.approx(1.0)


# ============================================================
# nucleo/vectorizacion — coseno_dispersos()
# ============================================================

class TestCosenoDispersos:
    """coseno_dispersos entre vectores dispersos en [−1, 1], con guarda de nulo."""

    def test_vectores_identicos(self):
        v = {"x": 1.0, "y": 2.0}
        assert coseno_dispersos(v, v) == pytest.approx(1.0)

    def test_vectores_ortogonales(self):
        a = {"x": 1.0}
        b = {"y": 1.0}
        assert coseno_dispersos(a, b) == pytest.approx(0.0)

    def test_vector_nulo_devuelve_cero(self):
        a = {}
        b = {"x": 1.0}
        assert coseno_dispersos(a, b) == pytest.approx(0.0)

    def test_vectores_proporcionales(self):
        a = {"x": 1.0, "y": 2.0}
        b = {"x": 2.0, "y": 4.0}
        assert coseno_dispersos(a, b) == pytest.approx(1.0)

    def test_rango_entre_menos_uno_y_uno(self):
        a = {"x": 3.0, "y": -1.0}
        b = {"x": -1.0, "y": 2.0}
        resultado = coseno_dispersos(a, b)
        assert -1.0 <= resultado <= 1.0


# ============================================================
# nucleo/corpus — estadisticas_corpus()
# ============================================================

class TestEstadisticasCorpus:
    """estadisticas_corpus resume el vocabulario y longitudes de abstracts."""

    # Artículos sintéticos con abstracts en inglés para usar el pipeline real.
    ARTICULOS = [
        {"id": 1, "abstract": "Machine learning models improve education outcomes for students."},
        {"id": 2, "abstract": "Deep learning models improve student learning outcomes in education."},
        {"id": 3, "abstract": "Generative artificial intelligence changes creative writing practice."},
    ]

    def test_total(self):
        from app.nucleo.corpus import estadisticas_corpus
        resultado = estadisticas_corpus(self.ARTICULOS)
        assert resultado["total"] == 3

    def test_vocabulario_total_es_positivo(self):
        from app.nucleo.corpus import estadisticas_corpus
        resultado = estadisticas_corpus(self.ARTICULOS)
        assert resultado["vocabulario_total"] > 0

    def test_tokens_min_menor_o_igual_a_max(self):
        from app.nucleo.corpus import estadisticas_corpus
        resultado = estadisticas_corpus(self.ARTICULOS)
        assert resultado["tokens_min"] <= resultado["tokens_max"]

    def test_tokens_promedio_en_rango(self):
        from app.nucleo.corpus import estadisticas_corpus
        resultado = estadisticas_corpus(self.ARTICULOS)
        assert resultado["tokens_min"] <= resultado["tokens_promedio"] <= resultado["tokens_max"]

    def test_corpus_vacio(self):
        from app.nucleo.corpus import estadisticas_corpus
        resultado = estadisticas_corpus([])
        assert resultado == {
            "total": 0,
            "tokens_promedio": 0,
            "tokens_min": 0,
            "tokens_max": 0,
            "vocabulario_total": 0,
        }

    def test_un_solo_articulo(self):
        from app.nucleo.corpus import estadisticas_corpus
        articulo = [{"id": 1, "abstract": "AI transforms education learning systems."}]
        resultado = estadisticas_corpus(articulo)
        assert resultado["total"] == 1
        # Con un solo artículo, min == promedio == max
        assert resultado["tokens_min"] == resultado["tokens_max"]
        assert resultado["tokens_promedio"] == resultado["tokens_min"]

    def test_vocabulario_no_repite_terminos(self):
        from app.nucleo.corpus import estadisticas_corpus
        # Dos artículos con el mismo abstract → vocabulario igual que con uno
        art = {"id": 1, "abstract": "AI learning education research methodology systems."}
        resultado_uno = estadisticas_corpus([art])
        resultado_dos = estadisticas_corpus([art, art])
        assert resultado_uno["vocabulario_total"] == resultado_dos["vocabulario_total"]

    def test_abstract_vacio_cuenta_cero_tokens(self):
        from app.nucleo.corpus import estadisticas_corpus
        articulos = [
            {"id": 1, "abstract": ""},
            {"id": 2, "abstract": "AI education learning research."},
        ]
        resultado = estadisticas_corpus(articulos)
        assert resultado["tokens_min"] == 0
