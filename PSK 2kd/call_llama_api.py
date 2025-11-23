def call_llama_api(query):
    try:
        # Prompt for extracting food items.
        prompt = (
            "Pavyzdys:\n"
            "---EXAMPLE---\n"
            "Šiandien vakare valgiau kebabą su česnakiniu padažu. Ryte, atsikėlęs valgiau cepelinus su kiauliena.\n"
            "Atsakymas turėtų būti:\n"
            "- Patiekalas: Kebabas su česnakiniu padažu\n"
            "- Patiekalas: Cepelinai su kiauliena\n"
            "---END EXAMPLE---\n\n"
            "Patvarkyk rašybos klaidas, žodžių galūnes, kad būtų lietuviškos.\n"
            "Išrink tik maisto produktus ir sudaryk patiekalus iš toliau pateikto teksto aprašymo, kuris pateikiamas lietuvių kalba. Jei nebuvo pateikta maisto patiekalų, neatsakyk į žinutę.\n"
            "Surašykite juos atskirai nuorodų formatu:\n\n"
            "---INPUT---\n"
            f"{query}\n"
            "---END INPUT---\n\n"
            "Formatuokite atsakymą kaip:\n"
            "- Patiekalas: [name]"
        )

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 300,
            "top_p": 1
        }

        # Send API request
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(data), verify=False)
        response.raise_for_status()

        # Extract response text
        result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"text": result}

    except requests.exceptions.RequestException as e:
        return {"error": f"Klaida jungiantis: {str(e)}"}
    except Exception as e:
        return {"error": f"Klaida, jungiantis prie API: {str(e)}"}