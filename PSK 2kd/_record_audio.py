def _record_audio(self, callback):
        try:
            device_info = sd.query_devices(kind='input')
            sample_rate = int(device_info['default_samplerate'])
            channels = device_info['max_input_channels']

            if channels < 1:
                raise ValueError("Mikrofono klaida")

            filename = self.audio_file_path
            silence_threshold = 500  # Garso jautrumas, keisti priklausomai nuo background noise
            silence_duration_limit = 2.0  # sekundes tylos
            silence_start_time = None

            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)

                def audio_callback(indata, frames, time_info, status):
                    nonlocal silence_start_time

                    if status:
                        print(f"Įrašinėjimo statusas: {status}")

                    gain = 10.0
                    amplified_data = np.clip(indata * gain, -32768, 32767).astype(np.int16)
                    wf.writeframes(amplified_data.tobytes())

                    # Compute RMS volume
                    rms = np.sqrt(np.mean(amplified_data.astype(np.float32) ** 2))
                    is_silent = rms < silence_threshold

                    if not is_silent:
                        silence_start_time = None  # Reset silence timer
                    else:
                        if silence_start_time is None:
                            silence_start_time = time.time()
                        elif time.time() - silence_start_time >= silence_duration_limit:
                            print("🛑 Aptikta tyla – stabdome įrašymą.")
                            self.is_recording = False
                            raise sd.CallbackStop()

                    if not self.is_recording:
                        raise sd.CallbackStop()
                with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='int16', callback=audio_callback):

                    print("🔴 Įrašymas pradėtas (kalbėkite)...")
                    start_time = time.time()
                    while self.is_recording:
                        sd.sleep(200)
                        if time.time() - start_time > self.MAX_RECORDING_DURATION:
                            self.is_recording = False
                            raise ValueError("Įrašymas per ilgas (max 30s)")

            if self._is_audio_file_empty(filename):
                raise ValueError("Audio failas tuščias. Įrašymo klaida!")

            recording_length = self._get_audio_length(filename)
            if recording_length > self.MAX_RECORDING_DURATION:
                raise ValueError(f"Įrašymas per ilgas: ({recording_length:.2f} s). Max {self.MAX_RECORDING_DURATION}s.")
            if recording_length < 3:
                raise ValueError(f"Įrašymas per trumpas: ({recording_length:.2f} s). Min {self.MIN_RECORDING_DURATION}s.")
            too_large, file_size_bytes = self.check_file_size(filename)
            if too_large:
                raise ValueError(f"Failo dydis per didelis: ({file_size_bytes / 1024:.2f} KB). Max leidžiamas dydis – 6 MB.")

        
            result = self._run_transcription()
            Clock.schedule_once(lambda dt: callback(result))

        except Exception as e:
            error_message = f"Klaida įrašymo metu: {e}"
            print(error_message)
            Clock.schedule_once(lambda dt: callback(error_message))