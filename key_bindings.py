from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.manager import KeyBindingManager

__all__ = (
    'mycli_bindings'
)
def mycli_bindings():

    key_binding_manager = KeyBindingManager(
        enable_open_in_editor=True,
        enable_system_bindings=True,
        enable_auto_suggest_bindings=True,
        enable_search=True,
        enable_abort_and_exit_bindings=True)

    @key_binding_manager.registry.add_binding(Keys.Tab)
    def _(event):
        """
        Force autocompletion at cursor.
        """
        #print('Detected <Tab> key.')
        b = event.cli.current_buffer
        #print b.complete_state
        if b.complete_state:
            b.complete_next()
        else:
            event.cli.start_completion(select_first=True)
    return key_binding_manager