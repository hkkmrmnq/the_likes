// import { createStore } from "zustand/vanilla";
// import { persist } from "zustand/middleware";
// import { useStore } from "zustand";

// interface LastBootstrapTimeState {
//   lastBootstrapTime: number;
//   updateLastBootstrapTime: () => void;
//   clearLastBootstrapTime: () => void;
// }

// const lastBootstrapTimeStore = createStore<LastBootstrapTimeState>()(
//   persist(
//     (set) => ({
//       lastBootstrapTime: 0,
//       updateLastBootstrapTime: () => {
//         set({
//           lastBootstrapTime: Date.now(),
//         });
//       },
//       clearLastBootstrapTime: () => {
//         set({
//           lastBootstrapTime: 0,
//         });
//       },
//     }),
//     {
//       name: "last-bootstrap-time-store",
//       partialize: (state) => ({
//         lastBootstrapTime: state.lastBootstrapTime,
//       }),
//     }
//   )
// );

// export const useLastBootstrapTimeStore = () => useStore(lastBootstrapTimeStore);
