"""
EditorPane NiceGUI component for AI draft editing with SFT logging and voice typing.

Layout:
- Top pane: Read-only AI Draft
- Bottom pane: User edit/dictation area with voice typing button
- Save & Log SFT button with toast notification
"""

import json
from pathlib import Path
from nicegui import ui


class EditorPane(ui.element):
    """
    A dual-pane editor component for AI-assisted writing with voice typing.
    """
    
    def __init__(self, sft_log_file=None):
        super().__init__()
        
        # SFT log file path
        if sft_log_file:
            self.sft_log_file = Path(sft_log_file)
        else:
            self.sft_log_file = Path.cwd() / "sft_pairs.jsonl"
        
        self._ai_textarea = None
        self._user_textarea = None
        self._save_button = None
        self._status_label = None
        self._voice_button = None
        self._is_recording = False
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the polished editor UI with vertical layout."""
        with self:
            with ui.column().classes('w-full gap-4'):
                # Action bar
                with ui.row().classes('w-full justify-between items-center'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('save', size='20px').classes('text-gray-600')
                        ui.label('Actions').classes('font-bold text-gray-700')
                    
                    self._save_button = ui.button(
                        'Save & Log SFT',
                        icon='save',
                        on_click=self._handle_save
                    ).props('color=positive')
                    self._save_button.disable()
                
                # Status label
                self._status_label = ui.label('').classes('text-sm')
                
                # Top pane: AI Draft (read-only)
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-blue-50 border-b'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('smart_toy', size='20px').classes('text-blue-600')
                            ui.label('AI Draft').classes('font-bold text-blue-800')
                            ui.label('Read-only').props('chip color=blue-200').classes('text-xs')
                    
                    with ui.card_section().classes('p-0'):
                        self._ai_textarea = ui.textarea() \
                            .classes('w-full') \
                            .props('readonly outlined') \
                            .style('min-height: 350px;')
                
                # Bottom pane: User Edit with voice typing
                with ui.card().classes('w-full'):
                    with ui.card_section().classes('bg-green-50 border-b'):
                        with ui.row().classes('items-center justify-between w-full'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('person', size='20px').classes('text-green-600')
                                ui.label('Your Edit').classes('font-bold text-green-800')
                                ui.label('Editable').props('chip color=green-200').classes('text-xs')
                            
                            # Voice typing button
                            self._voice_button = ui.button(
                                icon='mic',
                                on_click=self._toggle_voice_typing
                            ).props('round color=green').tooltip('Click to start/stop voice typing')
                            self._recording_label = ui.label('').classes('text-xs text-red-600 font-bold')
                    
                    with ui.card_section().classes('p-0'):
                        self._user_textarea = ui.textarea(
                            on_change=self._on_content_change
                        ).classes('w-full') \
                            .props('outlined') \
                            .style('min-height: 350px;')
                
                # Voice typing instructions
                with ui.row().classes('w-full justify-center'):
                    ui.markdown('🎤 **Voice Typing:** Click the microphone button and speak. Your words will appear in the text area above. Works best in Chrome/Edge browsers.') \
                        .classes('text-xs text-gray-500')
    
    def _on_content_change(self, e):
        """Handle content changes in user pane."""
        ai_val = self._ai_textarea.value if self._ai_textarea else ''
        user_val = self._user_textarea.value if self._user_textarea else ''
        if ai_val and user_val:
            self._save_button.disable(False)
        else:
            self._save_button.disable(True)
    
    def _handle_save(self):
        """
        Handle save button click.
        Logs SFT pair to JSONL file with toast notification.
        """
        ai_text = self._ai_textarea.value if self._ai_textarea else ''
        user_text = self._user_textarea.value if self._user_textarea else ''
        
        if not ai_text or not user_text:
            ui.notify('⚠️ Both panes must have content to save.', type='warning')
            return
        
        # Create SFT pair
        sft_pair = {
            "prompt": ai_text,
            "completion": user_text,
            "timestamp": str(Path.cwd())
        }
        
        # Append to JSONL file
        try:
            self._log_sft_pair(sft_pair)
            ui.notify('✓ SFT pair saved successfully!', type='positive',
                     caption=f'Logged to: {self.sft_log_file.name}')
            self._status_label.text = f'✓ Last saved: {Path.cwd().name}'
            self._status_label.classes('text-green-600')
        except Exception as e:
            ui.notify(f'✗ Error: {str(e)}', type='negative')
            self._status_label.text = f'✗ Error: {str(e)}'
            self._status_label.classes('text-red-600')
    
    def _log_sft_pair(self, sft_pair: dict):
        """Append an SFT pair to the JSONL log file."""
        self.sft_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.sft_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(sft_pair, ensure_ascii=False, indent=2) + '\n')
    
    def _toggle_voice_typing(self):
        """Toggle voice typing on/off using browser's Web Speech API."""
        self._is_recording = not self._is_recording
        
        if self._is_recording:
            # Start recording
            self._voice_button.props('color=red icon=mic_off')
            self._recording_label.text = '● Recording...'
            ui.notify('🎤 Voice typing started... Speak now!', type='info', timeout=3000)
            
            # JavaScript for Web Speech API
            ui.run_javascript('''
                if (!window.draftDaemonSpeech) {
                    window.draftDaemonSpeech = {
                        recognition: null,
                        textarea: null,
                        isRecording: false
                    };
                }
                
                const speech = window.draftDaemonSpeech;
                
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    speech.recognition = new SpeechRecognition();
                    speech.recognition.continuous = true;
                    speech.recognition.interimResults = true;
                    speech.recognition.lang = 'en-US';
                    
                    // Find the textarea element
                    speech.textarea = document.querySelector('[data-textarea="user"]');
                    if (!speech.textarea) {
                        speech.textarea = document.querySelectorAll('textarea')[1];
                    }
                    
                    speech.recognition.onresult = (event) => {
                        let finalTranscript = '';
                        for (let i = event.resultIndex; i < event.results.length; ++i) {
                            if (event.results[i].isFinal) {
                                finalTranscript += event.results[i][0].transcript + ' ';
                            }
                        }
                        if (finalTranscript && speech.textarea) {
                            const currentValue = speech.textarea.value || '';
                            speech.textarea.value = currentValue + finalTranscript;
                            // Trigger NiceGUI change event
                            speech.textarea.dispatchEvent(new Event('input', { bubbles: true }));
                            speech.textarea.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    };
                    
                    speech.recognition.onerror = (event) => {
                        console.error('Speech recognition error:', event.error);
                    };
                    
                    speech.recognition.start();
                    speech.isRecording = true;
                } else {
                    alert('Voice typing is not supported in your browser. Please use Chrome or Edge.');
                }
            ''')
        else:
            # Stop recording
            self._voice_button.props('color=green icon=mic')
            self._recording_label.text = ''
            ui.notify('✓ Voice typing stopped', type='positive', timeout=2000)
            
            # Stop JavaScript speech recognition
            ui.run_javascript('''
                if (window.draftDaemonSpeech && window.draftDaemonSpeech.recognition) {
                    window.draftDaemonSpeech.recognition.stop();
                    window.draftDaemonSpeech.isRecording = false;
                }
            ''')
    
    def set_ai_content(self, content: str):
        """Set the AI draft content."""
        if self._ai_textarea:
            self._ai_textarea.value = content
            user_val = self._user_textarea.value if self._user_textarea else ''
            if content and user_val:
                self._save_button.disable(False)
            else:
                self._save_button.disable(True)
    
    def get_contents(self) -> dict:
        """Get both AI and user content."""
        return {
            "ai_content": self._ai_textarea.value if self._ai_textarea else '',
            "user_content": self._user_textarea.value if self._user_textarea else ''
        }
