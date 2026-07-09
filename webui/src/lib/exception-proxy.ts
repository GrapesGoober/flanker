export class ExceptionProxy {
	private static showAlert() {
		if (confirm('Something went wrong. Please reload.')) {
			window.location.reload();
		}
	}

	static wrap<T extends object>(instance: T): T {
		return new Proxy(instance, {
			get(target, prop, _) {
				// Use class reflection to get all functions of instance
				const value = Reflect.get(target, prop, target);
				if (typeof value !== 'function') {
					return value;
				}

				// Wrap each function of the given instance with try-catch
				return (...args: unknown[]) => {
					try {
						const result = value.call(target, ...args);
						if (result instanceof Promise) {
							return result.catch((error) => {
								ExceptionProxy.showAlert();
								throw error;
							});
						}
						return result;
					} catch (error) {
						ExceptionProxy.showAlert();
						throw error;
					}
				};
			}
		});
	}
}
