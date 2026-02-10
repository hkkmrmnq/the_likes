"use client";

import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { ColumnToDropToProps } from "@/src/types";
import { SortableItem } from "./SortableItem";

export function ColumnToDropTo({
  id,
  items,
  borderColor,
}: ColumnToDropToProps) {
  const { setNodeRef } = useDroppable({
    id,
  });

  return (
    <div
      ref={setNodeRef}
      className={`min-h-[180px] border-2 ${borderColor} rounded-lg p-4 mb-4`}
    >
      <SortableContext items={items} strategy={verticalListSortingStrategy}>
        {items.map((cardId) => (
          <SortableItem key={cardId} id={cardId} title={cardId} />
        ))}
      </SortableContext>
    </div>
  );
}
