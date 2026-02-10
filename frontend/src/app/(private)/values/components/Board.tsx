"use client";

import { toast } from "sonner";
import { useState, useMemo } from "react";
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
  UniqueIdentifier,
} from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";

import { ValueLinks, ValueNamesColumns, Polarity } from "@/src/types";
import { ItemOverlay } from "./SortableItem";
import { ColumnToDropTo } from "./ColumnToDropTo";
import { useMoralProfileStore } from "@/src/stores";

function valuesToColumns(values: ValueLinks): ValueNamesColumns {
  const sortedValues = [...values].sort((a, b) => a.user_order - b.user_order);
  const result: ValueNamesColumns = {
    positive: [],
    neutral: [],
    negative: [],
  };
  for (const v of sortedValues) {
    result[v.polarity].push(v.value_name);
  }
  return result;
}

function columnsToValues(
  columns: ValueNamesColumns,
  values: ValueLinks,
  setValues: (new_values: ValueLinks) => void,
) {
  const newValues = [...values];
  const orderedColumns = {
    positive: columns.positive,
    neutral: columns.neutral,
    negative: columns.negative,
  };
  let userOrder = 0;
  for (const key in orderedColumns) {
    const polarity = key as keyof typeof orderedColumns;
    for (const item of orderedColumns[polarity]) {
      userOrder++;
      let found = false;
      for (const value of newValues) {
        if (item === value.value_name) {
          value.user_order = userOrder;
          value.polarity = polarity;
          found = true;
          break;
        }
      }
      if (!found) {
        const msg = `assignPolarityAndOrder error: board item "${item}" not found in values`;
        toast.error(msg);
        return;
      }
    }
  }
  setValues(newValues);
}

export function Board() {
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null);
  const { values, setValues, setHaveUnsavedChanges } = useMoralProfileStore();
  const columns = useMemo(() => valuesToColumns(values), [values]);
  const sensors = useSensors(useSensor(PointerSensor));

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeId = active.id.toString();
    const overId = over.id.toString();

    const activeColumn = findColumn(activeId, columns);

    const overColumn = isColumnId(overId)
      ? (overId as Polarity)
      : findColumn(overId, columns);

    if (!activeColumn || !overColumn) return;

    let newColumns: ValueNamesColumns;

    if (activeColumn === overColumn) {
      newColumns = {
        ...columns,
        [activeColumn]: arrayMove(
          columns[activeColumn],
          columns[activeColumn].indexOf(activeId),
          columns[activeColumn].indexOf(overId),
        ),
      };
    } else {
      const sourceItems = [...columns[activeColumn]];
      const destItems = [...columns[overColumn]];
      const activeIndex = sourceItems.indexOf(activeId);
      const [movedItem] = sourceItems.splice(activeIndex, 1);
      if (!movedItem) return;

      let insertIndex = destItems.length;
      if (!isColumnId(overId)) {
        const overIndex = destItems.indexOf(overId);
        if (overIndex >= 0) {
          insertIndex = overIndex;
        }
      }
      destItems.splice(insertIndex, 0, movedItem);

      newColumns = {
        ...columns,
        [activeColumn]: sourceItems,
        [overColumn]: destItems,
      };
    }

    columnsToValues(newColumns, values, setValues);
    setHaveUnsavedChanges(true);
  };

  const findColumn = (
    itemId: string,
    cols: ValueNamesColumns,
  ): Polarity | null => {
    if (cols.neutral.includes(itemId)) return "neutral";
    if (cols.positive.includes(itemId)) return "positive";
    if (cols.negative.includes(itemId)) return "negative";
    return null;
  };

  const isColumnId = (id: string): id is Polarity => {
    return ["neutral", "positive", "negative"].includes(id);
  };

  return (
    <div className="flex gap-8 p-6">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        {/* Left Side Container */}
        <div className="flex-1 flex items-center">
          {" "}
          <div className="w-full">
            <h2 className="text-xl font-bold mb-4 text-center">
              Neutral: indifferent
            </h2>
            <ColumnToDropTo
              id="neutral"
              items={columns.neutral}
              borderColor="border-gray-500"
            />
          </div>
        </div>

        {/* Right Side Container */}
        <div className="flex-1 justify-between">
          {/* Top Right */}
          <div>
            <h2 className="text-xl font-bold text-center text-cyan-500 py-3">
              Positive: the higher the better
            </h2>
            <ColumnToDropTo
              id="positive"
              items={columns.positive}
              borderColor="border-cyan-400"
            />
          </div>
          {/* Bottom Right */}
          <div>
            <ColumnToDropTo
              id="negative"
              items={columns.negative}
              borderColor="border-red-400"
            />
            <h2 className="text-xl font-bold text-center text-red-400">
              Negative: the lower the worse
            </h2>
          </div>
        </div>
        <DragOverlay style={{ cursor: "grabbing" }}>
          {activeId && <ItemOverlay title={activeId.toString()} />}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
