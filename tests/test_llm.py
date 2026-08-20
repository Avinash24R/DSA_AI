from Agent.nodes import get_llm


def test_groq_llm():

    llm = get_llm()

    response = llm.invoke(
        "Explain the sliding window technique in exactly 2 sentences."
    )

    print("\n========== GROQ RESPONSE ==========")
    print(response.content)

    assert response.content