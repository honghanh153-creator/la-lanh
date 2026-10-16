import { useEffect, useState } from "react";

export type RadarOwner = { epoch: string | null; isReady: boolean };
type EraseTarget = { id: string; label: string; epoch: string };

/**
 * One confirmed delete for every Radar path (invite, private check, owner result).
 * The target is bound to the owner epoch it was opened for: a different or not yet
 * verified owner never sees the sheet, and an owner change drops the target unasked.
 */
export function useRadarEraseTarget(owner: RadarOwner) {
  const [target, setTarget] = useState<EraseTarget | null>(null);

  useEffect(() => {
    setTarget((current) => (current && current.epoch !== owner.epoch ? null : current));
  }, [owner.epoch]);

  const open = target !== null && owner.isReady && target.epoch === owner.epoch;
  return {
    open,
    target: open ? target : null,
    request: (id: string, label: string) => {
      if (owner.isReady && owner.epoch) setTarget({ id, label, epoch: owner.epoch });
    },
    cancel: () => setTarget(null),
  };
}
