    def save_edited_product(self, product_id, popup):
        new_name = self.product_input.text.strip()
        if new_name is None:
            self.show_error("Pavadinimas negali būti tuščias.")
            return
        if len(new_name) > 255:
            self.show_error("Pavadinimas negali viršyti 255 simbolių.")
            return
        for product in PRODUCTS:
            if product["id"] == product_id:
                product["product_name"] = new_name
        popup.dismiss()
        self.update_product_list()