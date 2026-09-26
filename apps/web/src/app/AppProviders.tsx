import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { RouterProviderProps } from "react-router-dom";
import { RouterProvider } from "react-router-dom";

import { ThemeProvider } from "../shared/theme/ThemeProvider";
import { PERSONAL_DATA_CLEARED_EVENT } from "../shared/storage/clearPersonalData";

type AppProvidersProps = Pick<RouterProviderProps, "router">;

export function AppProviders({ router }: AppProvidersProps) {
  const [queryClient] = useState(() => new QueryClient({
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
  }));

  useEffect(() => {
    const clearQueries = () => queryClient.clear();
    window.addEventListener(PERSONAL_DATA_CLEARED_EVENT, clearQueries);
    return () => window.removeEventListener(PERSONAL_DATA_CLEARED_EVENT, clearQueries);
  }, [queryClient]);

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ThemeProvider>
  );
}
