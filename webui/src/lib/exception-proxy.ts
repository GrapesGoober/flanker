export class ExceptionProxy {
	static wrap<T extends object>(instance: T): T {
		return new Proxy(instance, {
			get(target, prop, _) {
				// Use class reflection to get all functions of instance
				const value = Reflect.get(target, prop, target);
				if (typeof value !== 'function') {
					return value;
				}

				// Bind function to instance itself so its behaviour is the same
				const fn = value.bind(target);

				// Proxy each arbitrary function of instance with try-catch
				return (...args: unknown[]) => {
					try {
						const result = fn(...args);
						if (result instanceof Promise) {
							return result.catch((error) => {
								alert('Something went wrong');
								throw error;
							});
						}
						return result;
					} catch (error) {
						alert('Something went wrong');
						throw error;
					}
				};
			}
		});
	}
}
