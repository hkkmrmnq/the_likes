import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

interface SortableItemProps {
  id: string;
  title: string;
}

export function SortableItem({ id, title }: SortableItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id });

  const dynamicStyle = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={dynamicStyle}
      className="
        p-4
        my-2
        font-bold
        border
        rounded
        cursor-grab
        select-none
        active:cursor-grabbing
        shadow-sm
        transition-colors
      "
      {...attributes}
      {...listeners}
    >
      {title}
    </div>
  );
}

export function ItemOverlay({ title }: { title: string }) {
  return (
    <div
      className="
      p-4
      my-2
      border
      border-white
      rounded
      shadow-lg
      bg-gray-800
    "
    >
      <div className="font-bold">{title}</div>
    </div>
  );
}
