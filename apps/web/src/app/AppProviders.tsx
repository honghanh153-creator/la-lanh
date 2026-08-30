import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { RouterProviderProps } from "react-router-dom";
import { RouterProvider } from "react-router-dom";

type AppProvidersProps = Pick<RouterProviderProps, "router">;

export function AppProviders({ router }: AppProvidersProps) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: 1,
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
