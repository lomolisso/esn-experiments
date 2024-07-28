import base64
import gzip
import tempfile

class TFModelManager:
    """
    Handles the loading and inference of a TensorFlow model.
    Developers need to implement these methods according to their model and application.
    """
    _model = None
    _tf = None
    _np = None

    def update_model(self, tf_model_b64, tf_model_bytesize):
        """
        Update the model with a new model.
        """
        # Import modules if not already imported
        if self._tf is None:
            import tensorflow as tf
            self._tf = tf
        if self._np is None:
            import numpy 
            self._np = numpy

        # Decode b64 encoded gzipped model into bytes
        _decoded_model = base64.b64decode(tf_model_b64)

        # Decompress the model
        _decoded_model = gzip.decompress(_decoded_model)

        # Check if the model size matches the expected size
        if len(_decoded_model) != tf_model_bytesize:
            raise ValueError(
                f"Model size mismatch: expected {tf_model_bytesize} bytes, got {len(_decoded_model)} bytes"
            )
        
        # Load the model
        self._model = self._tf.lite.Interpreter(model_content=_decoded_model)
        self._model.allocate_tensors()

        # Get input and output tensors.
        self._input_details = self._model.get_input_details()
        self._output_details = self._model.get_output_details()
        print(f"Model loaded successfully. Input shape: {self._input_details[0]['shape']}, Output shape: {self._output_details[0]['shape']}")


    def predict(self, input_data):
        """
        Performs inference using the current model loaded in the manager.
        Calls the _preprocess_input method on the input data, then runs the model,
        and finally calls the _postprocess_output method on the output data.
        """

        # Check if the model is loaded
        if self._model is None:
            raise ValueError("Model is not loaded")
        
        # Preprocess the input
        input_data = self._preprocess_input(input_data)

        # Add batch dimension if the model expects it
        input_data = self._np.expand_dims(input_data, axis=0).astype(self._input_details[0]['dtype'])   

        # Set the value for the model's input
        self._model.set_tensor(self._input_details[0]['index'], input_data)

        # Run the model
        self._model.invoke()

        # Extract the output data from the tensor
        output_data = self._model.get_tensor(self._output_details[0]['index'])
        
        # Postprocess the output
        return self._postprocess_output(output_data)

    def _preprocess_input(self, input_data):
        """
        Preprocesses the input data before feeding it to the model.
        """

        # Check if the model requires quantized input
        if self._input_details[0]['dtype'] == self._np.uint8:
            # Quantize the input
            scale, zero_point = self._input_details[0]['quantization']
            input_data = input_data / scale + zero_point
            #input_data = self._np.clip(input_data, 0, 256)
            return input_data

        return input_data


    def _postprocess_output(self, output_data):
        """
        Postprocesses the output data after getting it from the model.
        """

        return self._np.argmax(output_data)