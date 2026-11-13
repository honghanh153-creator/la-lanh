// Adapted from Codex review r30 probes for #83: revoked readings must not survive in any cache.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiProblem, getSession, getReceivedRadarResult, getPublicRadarInvite, getRadarReceipt, withdrawReceivedRadar, withdrawRadarByInvite, type RadarResult } from "../../shared/api/client";
import { RadarReceivedResultPage } from "./RadarReceivedPage";
import { RadarReceiptPage } from "./RadarReceiptPage";
import { PublicRadarPage } from "./PublicRadarPage";

vi.mock("../../shared/api/client", async (loadOriginal) => ({
  ...await loadOriginal<typeof import("../../shared/api/client")>(),
  currentSessionEpoch: vi.fn(() => "recipient-session"),
  getSession: vi.fn(), getReceivedRadarResult: vi.fn(), getRadarReceipt: vi.fn(),
  getPublicRadarInvite: vi.fn(), withdrawReceivedRadar: vi.fn(), withdrawRadarByInvite: vi.fn(),
}));
const result: RadarResult = {
 request_id:"request-a", mode:"consented_invite", version:"radar-result-v1",
 headline:"SYNTHETIC REVOKED READING",summary:"Synthetic summary",
 dimensions:[{key:"communication",label:"Giao tiếp",signal:"Có tín hiệu",body:"Synthetic body",evidence_ids:[]}],strongest_contacts:[],disclaimer:"Synthetic only",
};
function view(client:QueryClient,path:string){
 return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><Routes>
  <Route element={<RadarReceivedResultPage/>} path="/radar/received/:requestId"/>
  <Route element={<RadarReceiptPage/>} path="/radar/receipt"/>
  <Route element={<PublicRadarPage/>} path="/radar/i/:token"/>
 </Routes></MemoryRouter></QueryClientProvider>);
}
describe("Codex R30 revoked local result representations",()=>{
 beforeEach(()=>{
  vi.clearAllMocks();
  vi.mocked(getSession).mockResolvedValue({csrf_token:"synthetic",expires_at:"2027-12-01T00:00:00Z",onboarding_status:"complete",resumed:true,session_epoch:"recipient-session",state:"active"});
  vi.mocked(getReceivedRadarResult).mockResolvedValue(result);
  vi.mocked(withdrawReceivedRadar).mockResolvedValue(undefined);
  vi.mocked(withdrawRadarByInvite).mockResolvedValue(undefined);
  vi.mocked(getPublicRadarInvite).mockRejectedValue(new Error("404"));
  vi.mocked(getRadarReceipt).mockRejectedValue(new ApiProblem(404,"RADAR_UNAVAILABLE","Unavailable"));
 });
 it("hides a cached recipient reading once the server says it was revoked",async()=>{
  const client=new QueryClient({defaultOptions:{queries:{retry:false,staleTime:0}}});
  client.setQueryData(["radar-received-result","recipient-session","request-a"],result);
  vi.mocked(getReceivedRadarResult).mockRejectedValue(new ApiProblem(404,"RADAR_UNAVAILABLE","Unavailable"));
  view(client,"/radar/received/request-a");
  await waitFor(()=>expect(client.getQueryState(["radar-received-result","recipient-session","request-a"])?.status).toBe("error"));
  expect(screen.queryByText(result.headline)).not.toBeInTheDocument();
 });
 it("received withdrawal also prevents reopening the same cached receipt",async()=>{
  const client=new QueryClient({defaultOptions:{queries:{retry:false,staleTime:30000}}});
  client.setQueryData(["radar-receipt"],result);
  const rendered=view(client,"/radar/received/request-a");
  await userEvent.click(await screen.findByRole("button",{name:"Rút chart của tôi khỏi kết quả này"}));
  await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button",{name:"Rút chart"}));
  await screen.findByRole("heading",{name:"Chart của bạn đã được rút."});
  rendered.unmount();view(client,"/radar/receipt");
  expect(screen.queryByText(result.headline)).not.toBeInTheDocument();
 });
 it("token withdrawal prevents reopening the same cached recipient result",async()=>{
  const client=new QueryClient({defaultOptions:{queries:{retry:false,staleTime:30000}}});
  client.setQueryData(["radar-received-result","recipient-session","request-a"],result);
  const rendered=view(client,"/radar/i/synthetic-token");
  await userEvent.click(await screen.findByRole("button",{name:"Rút chart khỏi kết quả"}));
  await userEvent.click(within(await screen.findByRole("dialog")).getByRole("button",{name:"Rút chart"}));
  await screen.findByRole("heading",{name:"Chart của bạn đã được rút."});
  vi.mocked(getReceivedRadarResult).mockRejectedValue(new ApiProblem(404,"RADAR_UNAVAILABLE","Unavailable"));
  rendered.unmount();view(client,"/radar/received/request-a");
  await waitFor(()=>expect(screen.queryByText("Đang mở lại bản đọc của bạn…")).not.toBeInTheDocument());
  expect(screen.queryByText(result.headline)).not.toBeInTheDocument();
 });
});
