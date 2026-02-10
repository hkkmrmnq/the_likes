"use client";

import { toast } from "sonner";

import { useEffect, useState } from "react";

import { LanguageSelector } from "./LanguageSelector";
import * as profileService from "@/src/api/profile";
import { handleErrorInComponent } from "@/src/utils";
import { useLoadingStore, useProfileStore } from "@/src/stores";
import { ActionButton } from "@/src/components/Buttons";
import { buttonThinColored } from "@/src/styles";

export default function ProfilePage() {
  const {
    setUserId,
    name,
    setName,
    languages,
    setLanguages,
    latitude,
    setLatitude,
    longitude,
    setLongitude,
    distance_limit,
    setDistanceLimit,
    recommend_me,
    setRecommendMe,
  } = useProfileStore();
  const { isLoading, stopLoading } = useLoadingStore();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await profileService.getProfile();
        const fetchedProfile = response.data;
        setUserId(fetchedProfile.user_id);
        setName(fetchedProfile.name);
        setLanguages(fetchedProfile.languages);
        setLatitude(fetchedProfile.latitude);
        setLongitude(fetchedProfile.longitude);
        setDistanceLimit(fetchedProfile.distance_limit);
        setRecommendMe(fetchedProfile.recommend_me);
      } catch (err) {
        handleErrorInComponent(err, setError);
      } finally {
        stopLoading();
      }
    };

    loadProfile();
  }, [
    setUserId,
    setName,
    setLanguages,
    setLatitude,
    setLongitude,
    setDistanceLimit,
    setRecommendMe,
    stopLoading,
  ]);

  const detectLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by this browser");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
      },
      (error) => {
        alert("Unable to retrieve your location: " + error.message);
      },
    );
  };

  const submit = async () => {
    setError("");
    setFieldErrors({});

    try {
      const newData = {
        name,
        languages,
        longitude,
        latitude,
        distance_limit,
        recommend_me,
      };
      const response = await profileService.submitProfile(newData);
      toast.info(response.message);
    } catch (err) {
      handleErrorInComponent(err, setError, setFieldErrors);
    } finally {
      stopLoading();
    }
  };

  if (isLoading) {
    return <>Loading...</>;
  }

  return (
    <>
      <div className="h-full py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">Your Profile</h1>
            <p className="mt-2 text-gray-300">
              Update your profile information
            </p>
          </div>

          <div className="space-y-6">
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-center"
              >
                Name
              </label>
              <div className="mt-1">
                <input
                  id="name"
                  name="name"
                  type="text"
                  value={name || ""}
                  onChange={(e) => setName(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 text-center"
                  placeholder="Enter your name"
                />
                {fieldErrors && fieldErrors.name && (
                  <p className="text-red-500 text-sm mt-1">
                    {fieldErrors.name}
                  </p>
                )}
              </div>
            </div>

            <LanguageSelector
              languages={languages}
              setLanguages={setLanguages}
            />
            {fieldErrors && fieldErrors.languages && (
              <p className="text-red-500 text-sm mt-1">
                {fieldErrors.languages}
              </p>
            )}

            {/* Location section */}
            <div>
              <label className="block text-sm font-medium text-center mb-3">
                Location
              </label>

              {/* Detect Location Button */}
              <div className="text-center mb-4">
                <button
                  type="button"
                  onClick={detectLocation}
                  className="cursor-pointer bg-cyan-600 text-white px-4 py-2 rounded-lg hover:bg-cyan-700 transition-colors text-sm"
                >
                  Detect Location
                </button>
                {/* Help text */}
                <p className="text-xs text-gray-400 text-center mt-2">
                  Click Detect Location or enter coordinates manually
                </p>
              </div>

              {/* Latitude and Longitude Fields */}
              <div className="flex space-x-4">
                <div className="flex-1">
                  <label
                    htmlFor="latitude"
                    className="block text-xs text-center mb-1"
                  >
                    Latitude
                  </label>
                  <input
                    id="latitude"
                    type="number"
                    step="any"
                    value={(!!latitude && latitude.toString()) || ""}
                    onChange={(e) => setLatitude(parseFloat(e.target.value))}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 text-center"
                    placeholder="e.g., 28.359381"
                  />
                  {fieldErrors && fieldErrors.latitude && (
                    <p className="text-red-500 text-sm mt-1">
                      {fieldErrors.latitude}
                    </p>
                  )}
                </div>

                <div className="flex-1">
                  <label
                    htmlFor="longitude"
                    className="block text-xs text-center mb-1"
                  >
                    Longitude
                  </label>
                  <input
                    id="longitude"
                    type="number"
                    step="any"
                    value={(!!longitude && longitude.toString()) || ""}
                    onChange={(e) => setLongitude(parseFloat(e.target.value))}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 text-center"
                    placeholder="e.g., 129.595943"
                  />
                  {fieldErrors && fieldErrors.longitude && (
                    <p className="text-red-500 text-sm mt-1">
                      {fieldErrors.longitude}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Distance Limit */}
            <div>
              <label
                htmlFor="distanceLimit"
                className="block text-sm font-medium text-center mb-3"
              >
                Distance Limit (km)
              </label>
              <div className="text-center">
                <input
                  id="distanceLimit"
                  type="number"
                  min="1"
                  value={!distance_limit ? "" : distance_limit}
                  onChange={(e) => setDistanceLimit(parseFloat(e.target.value))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-cyan-500 focus:border-cyan-500 text-center"
                  placeholder="Enter distance in kilometers"
                />
                {fieldErrors && fieldErrors.distance_limit && (
                  <p className="text-red-500 text-sm mt-1">
                    {fieldErrors.distance_limit}
                  </p>
                )}
              </div>
              <p className="text-xs text-gray-400 text-center mt-2">
                Leave empty if no needed
              </p>
            </div>

            {/* Recommend Me Toggle */}
            <div className="text-center">
              <div className="flex items-center justify-center space-x-3">
                <span className="text-sm font-medium">Recommend me</span>
                <button
                  type="button"
                  onClick={() => setRecommendMe(!recommend_me)}
                  className={`
                    relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2
                    ${recommend_me ? "bg-cyan-600" : "bg-gray-200"}
                  `}
                >
                  <span className="sr-only">Recommend me</span>
                  <span
                    className={`
                      pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
                      ${recommend_me ? "translate-x-5" : "translate-x-0"}
                    `}
                  />
                </button>
              </div>
              <p className="text-xs text-gray-300 mt-2">
                {recommend_me
                  ? "Your profile will be visible to others"
                  : "Your profile will be hidden from others"}
              </p>
            </div>

            {/* Submit button */}
            <div className="text-center">
              <ActionButton
                label="Update profile"
                loadingIndication="Updating..."
                action={submit}
                className={buttonThinColored}
              />
            </div>
          </div>

          {error && <div className="text-red-500 text-sm mt-1">{error}</div>}
        </div>
      </div>
    </>
  );
}
