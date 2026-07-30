from sdk import SDKPlugin, SDKPluginManager, PluginResult

class EchoPlugin(SDKPlugin):
    name = "echo"
    def execute(self, context=None, **kwargs):
        return PluginResult(self.manifest.name, output=kwargs.get("text", ""))

manager = SDKPluginManager()
manager.register(EchoPlugin())
print(manager.execute("echo", text="hello").output)
