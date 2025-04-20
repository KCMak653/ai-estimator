class ValidConfigGenerator:
    """
    The purpose of this class is to generate a valid configuration from freetext which exists in the pricing keyspace

    """
    def __init__(self, pricing_json):
        self.valid_keyspace = generate_keyspace(pricing_json)

    def generate_keyspace(self, pricing_json):


        """
        
Ideas: 
    window_type:
    axis_1:
    axis_2:
    



        """